from typing import List, Dict, Any, Optional
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from ..tools.interfaces import SlackClient
from ..config import settings

class LiveSlackClient(SlackClient):
    """Live Slack API Client using Slack WebClient."""

    def __init__(self):
        token = settings.SLACK_BOT_TOKEN.strip()
        if not token or token == "xoxb-placeholder":
            raise ValueError("SLACK_BOT_TOKEN is not configured or is a placeholder.")
        self.client = WebClient(token=token)
        self._channel_cache: Dict[str, str] = {}

    def _resolve_channel_id(self, channel_name: str) -> Optional[str]:
        clean_name = channel_name.strip().lstrip("#").lower()
        if (channel_name.startswith("C") or channel_name.startswith("G")) and len(channel_name) >= 9:
            return channel_name

        if clean_name in self._channel_cache:
            return self._channel_cache[clean_name]

        try:
            # Query public channels only — does not require groups:read scope
            res = self.client.conversations_list(types="public_channel", limit=100)
            channels = res.get("channels", [])
            for ch in channels:
                name = (ch.get("name") or "").lower()
                c_id = ch.get("id")
                if name and c_id:
                    self._channel_cache[name] = c_id

            # 1. Exact match
            if clean_name in self._channel_cache:
                return self._channel_cache[clean_name]

            # 2. Singular / plural matching (e.g. "internships" -> "internship")
            clean_stem = clean_name.rstrip("s")
            for ch_name, c_id in self._channel_cache.items():
                if ch_name.rstrip("s") == clean_stem:
                    return c_id

            # 3. Substring matching
            for ch_name, c_id in self._channel_cache.items():
                if clean_stem in ch_name or ch_name in clean_stem:
                    return c_id
        except Exception as e:
            print(f"[SlackLive] Error querying public channels: {e}")

        return self._channel_cache.get(clean_name)

    def search_billing_messages(self, query: str, channel: str = "billing") -> List[Dict[str, Any]]:
        channel_id = self._resolve_channel_id(channel)
        if not channel_id:
            if channel.startswith("C") or channel.startswith("G"):
                channel_id = channel
            else:
                print(f"[SlackLive] Warning: Channel #{channel} could not be resolved to a channel ID.")
                return []

        try:
            # Attempt to fetch channel history
            res = self.client.conversations_history(channel=channel_id, limit=30)
            messages = res.get("messages", [])
        except SlackApiError as e:
            err = e.response.get("error")
            if err == "not_in_channel":
                # Attempt to join channel if permissions allow
                try:
                    self.client.conversations_join(channel=channel_id)
                    res = self.client.conversations_history(channel=channel_id, limit=30)
                    messages = res.get("messages", [])
                except Exception:
                    print(f"[SlackLive] RECON Bot is not a member of #{channel} (ID: {channel_id}). Please invite the bot to the channel in Slack by typing: /invite @Recon")
                    return []
            else:
                print(f"[SlackLive] Slack API Error fetching history: {err}")
                return []

        query_lower = query.lower()
        normalized = []
        for m in messages:
            text = m.get("text", "")
            # If query keywords or general billing terms match
            if any(term in text.lower() for term in [query_lower, "billing", "charge", "refund", "subscription", "fee", "duplicate", "timeout"]):
                # Try to extract human author name if available
                author_name = m.get("username")
                if not author_name and "user_profile" in m:
                    author_name = m["user_profile"].get("real_name") or m["user_profile"].get("display_name")
                if not author_name:
                    author_name = m.get("user", "slack_team_member")

                normalized.append({
                    "source": "slack",
                    "channel": f"#{channel.lstrip('#')}",
                    "message_id": m.get("ts", ""),
                    "timestamp": datetime.fromtimestamp(float(m.get("ts", 0))).isoformat() + "Z" if m.get("ts") else "",
                    "author": author_name,
                    "text": text
                })
        return normalized

    def post_message(self, channel: str, text: str) -> Dict[str, Any]:
        channel_id = self._resolve_channel_id(channel)
        target = channel_id or (channel if channel.startswith("#") or channel.startswith("C") else f"#{channel}")
        try:
            res = self.client.chat_postMessage(channel=target, text=text)
            return {
                "ok": True,
                "channel": res.get("channel"),
                "message": {
                    "source": "slack",
                    "channel": target,
                    "message_id": res.get("ts"),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "author": "RECON Bot",
                    "text": text
                }
            }
        except SlackApiError as e:
            err = e.response.get("error", str(e))
            print(f"[SlackLive] Slack API Error posting message to {target}: {err}")
            # If target channel was not found or bot not in channel, fallback to #general
            clean_ch = channel.strip().lstrip("#").lower()
            if err in ["channel_not_found", "not_in_channel", "is_archived"] and clean_ch != "general":
                gen_id = self._resolve_channel_id("general")
                if gen_id and gen_id != target:
                    try:
                        res = self.client.chat_postMessage(
                            channel=gen_id,
                            text=f"_[RECON notice: forwarded to #general because bot is not in #{clean_ch}]_\n\n{text}"
                        )
                        return {
                            "ok": True,
                            "channel": res.get("channel"),
                            "note": f"Forwarded to #general (bot is not in #{clean_ch})",
                            "message": {
                                "source": "slack",
                                "channel": gen_id,
                                "message_id": res.get("ts"),
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "author": "RECON Bot",
                                "text": text
                            }
                        }
                    except Exception as fallback_err:
                        print(f"[SlackLive] Fallback to general failed: {fallback_err}")

            raise RuntimeError(f"Slack postMessage failed for '{channel}': {err}")
