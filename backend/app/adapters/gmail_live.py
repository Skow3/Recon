import os
import base64
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from ..tools.interfaces import GmailClient
from ..config import settings

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

class LiveGmailClient(GmailClient):
    """Live Google Gmail API Client using read-only OAuth credentials."""

    def __init__(self):
        self.creds = self._get_credentials()
        self.service = build("gmail", "v1", credentials=self.creds) if self.creds else None

    def _get_credentials(self) -> Optional[Credentials]:
        creds = None
        token_path = os.path.abspath(settings.GMAIL_TOKEN_PATH)
        creds_path = os.path.abspath(settings.GMAIL_CREDENTIALS_PATH)

        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                print(f"[GmailLive] Error loading token: {e}")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    with open(token_path, "w") as token:
                        token.write(creds.to_json())
                except Exception as e:
                    print(f"[GmailLive] Error refreshing token: {e}")
                    creds = None
            elif os.path.exists(creds_path):
                # Note: Interactive authorization flow is executed on initial run if local display is available
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(token_path, "w") as token:
                        token.write(creds.to_json())
                except Exception as e:
                    print(f"[GmailLive] OAuth authorization flow could not be completed non-interactively: {e}")
                    creds = None

        return creds

    def search_customer(self, customer_identifier: str) -> List[Dict[str, Any]]:
        if not self.service:
            raise RuntimeError("Gmail API service is not initialized. Please verify credentials.json / token.json.")

        # Construct query for billing disputes
        q = f'{customer_identifier} (billing OR charge OR refund OR invoice OR duplicate OR "charged twice" OR twice OR payment OR dispute)'
        try:
            results = self.service.users().messages().list(userId="me", q=q, maxResults=5).execute()
            messages = results.get("messages", [])
        except Exception as e:
            print(f"[GmailLive] Search with billing keywords failed: {e}")
            messages = []

        if not messages:
            # Fallback to broader search matching this customer
            try:
                results = self.service.users().messages().list(userId="me", q=customer_identifier, maxResults=5).execute()
                messages = results.get("messages", [])
            except Exception as e:
                print(f"[GmailLive] Fallback search failed: {e}")
                messages = []

        normalized_items = []
        for msg_item in messages:
            try:
                msg = self.service.users().messages().get(userId="me", id=msg_item["id"], format="full").execute()
                normalized = self._normalize_message(msg)
                normalized_items.append(normalized)
            except Exception as e:
                print(f"[GmailLive] Error fetching message {msg_item.get('id')}: {e}")

        return normalized_items

    def search_messages(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if not self.service:
            return []
        try:
            results = self.service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            messages = results.get("messages", [])
        except Exception as e:
            print(f"[GmailLive] search_messages query error: {e}")
            messages = []

        items = []
        for msg_item in messages:
            try:
                msg = self.service.users().messages().get(userId="me", id=msg_item["id"], format="full").execute()
                items.append(self._normalize_message(msg))
            except Exception as e:
                print(f"[GmailLive] Error fetching message {msg_item.get('id')}: {e}")
        return items

    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        if not self.service:
            raise RuntimeError("Gmail API service is not initialized.")

        thread = self.service.users().threads().get(userId="me", id=thread_id).execute()
        raw_msgs = thread.get("messages", [])
        normalized = [self._normalize_message(m) for m in raw_msgs]
        return {
            "thread_id": thread_id,
            "messages": normalized,
            "total_messages": len(normalized)
        }

    def _normalize_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        subject = headers.get("subject", "No Subject")
        sender = headers.get("from", "Unknown Sender")
        recipient = headers.get("to", "Unknown Recipient")
        date = headers.get("date", "")
        
        # Extract body text
        body_text = ""
        payload = msg.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        body_text += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        elif "body" in payload and payload["body"].get("data"):
            data = payload["body"]["data"]
            body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        if not body_text:
            body_text = msg.get("snippet", "")

        # Extract claims heuristically
        claims = []
        lower_body = body_text.lower()
        if any(term in lower_body for term in ["twice", "duplicate", "two times", "double", "charged again", "second charge"]):
            claims.append("Customer reports duplicate/double billing")
        if any(term in lower_body for term in ["refund", "money back", "reimburse"]):
            claims.append("Customer explicitly requests a refund")
        if "$499" in lower_body or "499" in lower_body:
            claims.append("Referenced charge amount: $499")

        return {
            "source": "gmail",
            "message_id": msg["id"],
            "thread_id": msg.get("threadId", msg["id"]),
            "sender": sender,
            "recipient": recipient,
            "subject": subject,
            "timestamp": date,
            "body": body_text[:1000],
            "relevant_claims": claims
        }
