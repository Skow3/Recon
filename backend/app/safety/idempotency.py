from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.case import ActionModel, VerificationModel
from ..tools.interfaces import StripeClient

class IdempotencyCheckResult:
    def __init__(self, is_duplicate: bool, reason: str, existing_refund_id: Optional[str] = None):
        self.is_duplicate = is_duplicate
        self.reason = reason
        self.existing_refund_id = existing_refund_id

def check_refund_idempotency(
    case_id: str,
    charge_id: str,
    amount: int,
    db: Session,
    stripe_client: StripeClient
) -> IdempotencyCheckResult:
    """
    Check both internal database action logs and external Stripe refunds
    to guarantee zero duplicate refunds.
    """
    # 1. Check local DB actions table
    existing_action = db.query(ActionModel).filter(
        ActionModel.case_id == case_id,
        ActionModel.charge_id == charge_id,
        ActionModel.status.in_(["succeeded", "completed", "executed"])
    ).first()

    if existing_action and existing_action.refund_id:
        return IdempotencyCheckResult(
            is_duplicate=True,
            reason=f"NO_DUPLICATE_ACTION: Case {case_id} already executed refund {existing_action.refund_id} for charge {charge_id}",
            existing_refund_id=existing_action.refund_id
        )

    # 2. Check local DB verifications table
    existing_verification = db.query(VerificationModel).filter(
        VerificationModel.case_id == case_id,
        VerificationModel.charge_id == charge_id,
        VerificationModel.verified == True
    ).first()

    if existing_verification:
        return IdempotencyCheckResult(
            is_duplicate=True,
            reason=f"NO_DUPLICATE_ACTION: Charge {charge_id} is already verified as refunded (Refund: {existing_verification.refund_id})",
            existing_refund_id=existing_verification.refund_id
        )

    # 3. Check Stripe directly for existing refunds on this charge
    try:
        stripe_refunds = stripe_client.list_refunds(charge_id=charge_id)
        for ref in stripe_refunds:
            if ref.get("status") == "succeeded" and ref.get("amount") >= amount:
                return IdempotencyCheckResult(
                    is_duplicate=True,
                    reason=f"NO_DUPLICATE_ACTION: Stripe already contains a succeeded refund {ref.get('id')} covering {amount} cents for charge {charge_id}",
                    existing_refund_id=ref.get("id")
                )
    except Exception as e:
        # If Stripe refund check fails, safety precaution: escalate
        return IdempotencyCheckResult(
            is_duplicate=True,
            reason=f"Cannot verify refund history in Stripe: {str(e)}",
            existing_refund_id=None
        )

    return IdempotencyCheckResult(is_duplicate=False, reason="Idempotency check passed: No prior refund found.")
