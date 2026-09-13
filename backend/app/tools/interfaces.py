from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class GmailClient(ABC):
    @abstractmethod
    def search_customer(self, customer_identifier: str) -> List[Dict[str, Any]]:
        """Search for threads and messages matching customer email, name, or keywords."""
        pass

    @abstractmethod
    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """Fetch complete thread details by ID."""
        pass


class StripeClient(ABC):
    @abstractmethod
    def find_customer(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find customer record by email or name."""
        pass

    @abstractmethod
    def list_charges(self, customer_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """List charges for a customer."""
        pass

    @abstractmethod
    def get_charge(self, charge_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve charge details by ID."""
        pass

    @abstractmethod
    def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve invoice details if available."""
        pass

    @abstractmethod
    def list_refunds(self, charge_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List existing refunds, optionally filtered by charge."""
        pass

    @abstractmethod
    def create_refund(
        self,
        charge_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a refund for a charge in Stripe TEST mode."""
        pass

    @abstractmethod
    def get_refund(self, refund_id: str) -> Dict[str, Any]:
        """Fetch and verify refund status from Stripe."""
        pass


class SlackClient(ABC):
    @abstractmethod
    def search_billing_messages(self, query: str, channel: str = "billing") -> List[Dict[str, Any]]:
        """Search recent messages in the billing channel related to the customer or dispute."""
        pass

    @abstractmethod
    def post_message(self, channel: str, text: str) -> Dict[str, Any]:
        """Post notification message to Slack channel."""
        pass
