import json
from typing import Optional, Dict, Any
from ..config import settings
from ..schemas.responses import ReconciliationResult, DecisionOutput, DecisionType

SYSTEM_PROMPT = """You are the reconciliation engine for RECON.
Your task is to analyze evidence from Gmail, Stripe, and Slack.
You must never invent evidence.
You must only use evidence supplied in the input.
You must choose exactly one decision:
- REFUND_RECOMMENDED
- NO_REFUND
- ESCALATE_FOR_REVIEW

A refund recommendation requires strong cross-system evidence.
Conflicting evidence or unsubstantiated claims must result in NO_REFUND or ESCALATE_FOR_REVIEW.
Do not expose chain-of-thought.
Return structured JSON only matching this schema:
{
  "decision": "REFUND_RECOMMENDED" | "NO_REFUND" | "ESCALATE_FOR_REVIEW",
  "confidence": 0.0 to 1.0,
  "reason": "concise evidence-based reason",
  "supporting_evidence": ["item 1", "item 2"],
  "risk_flags": ["flag 1"]
}
"""

class DecisionEngine:
    """Produces structured decisions from reconciled multi-app evidence."""

    def generate_decision(
        self,
        reconciliation: ReconciliationResult,
        stripe_error: Optional[str] = None,
        mock_mode: bool = False
    ) -> DecisionOutput:
        # If Stripe was unavailable, immediate escalation (never take financial actions blindly)
        if stripe_error:
            return DecisionOutput(
                decision=DecisionType.ESCALATE_FOR_REVIEW,
                confidence=0.99,
                reason=f"Stripe financial ledger is unavailable ({stripe_error}). Financial action blocked.",
                supporting_evidence=["Stripe unavailable"],
                risk_flags=["External financial ledger unreachable"]
            )

        # In mock mode, immediately use deterministic reasoning
        if mock_mode or settings.MOCK_MODE:
            return self._deterministic_reasoning(reconciliation)

        # If OpenAI API Key is configured and not empty, invoke LLM
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip() and not settings.OPENAI_API_KEY.startswith("your_"):
            try:
                return self._call_openai(reconciliation)
            except Exception as e:
                print(f"[DecisionEngine] OpenAI call failed: {e}. Falling back to deterministic reasoning.")

        # Deterministic evidence-based reasoning
        return self._deterministic_reasoning(reconciliation)

    def _call_openai(self, reconciliation: ReconciliationResult) -> DecisionOutput:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        user_content = json.dumps(reconciliation.model_dump(), indent=2)
        last_error = None

        create_kwargs = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this reconciled billing dispute evidence:\n{user_content}"}
            ]
        }

        # Temperature: Some models (like gpt-5-nano, o1, o3-mini) do not accept temperature != 1
        is_newer_reasoning_model = any(m in settings.OPENAI_MODEL.lower() for m in ["gpt-5", "o1", "o3", "nano"])
        if not is_newer_reasoning_model:
            create_kwargs["temperature"] = 0.1

        # Response format: Enable JSON mode where supported
        if any(m in settings.OPENAI_MODEL.lower() for m in ["gpt-4", "gpt-3.5"]):
            create_kwargs["response_format"] = {"type": "json_object"}

        for attempt in range(2):
            try:
                response = client.chat.completions.create(**create_kwargs)
                raw_text = response.choices[0].message.content
                data = json.loads(raw_text)
                
                # Validate decision
                dec_val = data.get("decision")
                if dec_val not in [d.value for d in DecisionType]:
                    dec_val = DecisionType.ESCALATE_FOR_REVIEW.value

                return DecisionOutput(
                    decision=DecisionType(dec_val),
                    confidence=float(data.get("confidence", 0.9)),
                    reason=str(data.get("reason", "")),
                    supporting_evidence=list(data.get("supporting_evidence", [])),
                    risk_flags=list(data.get("risk_flags", []))
                )
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                # If temperature was rejected by model, strip it and retry immediately
                if "temperature" in err_str and "temperature" in create_kwargs:
                    create_kwargs.pop("temperature", None)
                    continue
                # If response_format was rejected by model, strip it and retry immediately
                if "response_format" in err_str and "response_format" in create_kwargs:
                    create_kwargs.pop("response_format", None)
                    continue

                if attempt == 0:
                    user_content += f"\nNote: Previous response produced error: {str(e)}. Please return strictly valid JSON matching the schema."
                    create_kwargs["messages"][1]["content"] = f"Analyze this reconciled billing dispute evidence:\n{user_content}"
                    continue
                break

        # If both attempts fail, raise to allow fallback to deterministic reasoning
        raise RuntimeError(f"OpenAI call failed after retries: {last_error}")

    def _deterministic_reasoning(self, r: ReconciliationResult) -> DecisionOutput:
        # Check for already refunded
        already_refunded_contra = any("Already refunded" in c for c in r.contradictions)
        if already_refunded_contra:
            return DecisionOutput(
                decision=DecisionType.NO_REFUND,
                confidence=0.98,
                reason="A refund covering the duplicate charge already exists in Stripe. Duplicate action prevented.",
                supporting_evidence=r.refuting_evidence,
                risk_flags=["Existing refund detected"]
            )

        # Check for internal team disagreement
        if any("Internal team disagreement" in c for c in r.contradictions):
            return DecisionOutput(
                decision=DecisionType.ESCALATE_FOR_REVIEW,
                confidence=0.88,
                reason="Conflicting internal evidence in Slack regarding whether the second charge was an authorized service or accidental duplicate. Escalating for human investigation.",
                supporting_evidence=r.supporting_evidence[:2],
                risk_flags=r.risk_flags
            )

        # Check for legitimate charge conflict (false duplicate)
        if any("Legitimate charge conflict" in c for c in r.contradictions):
            return DecisionOutput(
                decision=DecisionType.NO_REFUND,
                confidence=0.96,
                reason="Although two $499 charges exist in Stripe, Slack internal business context documents that the second charge was a legitimate implementation fee agreed upon with the customer.",
                supporting_evidence=r.refuting_evidence,
                risk_flags=["Customer claim disputed by internal agreement"]
            )

        # Check for single charge conflict
        if any("Stripe record conflict" in c for c in r.contradictions) or r.charges_found == 1:
            return DecisionOutput(
                decision=DecisionType.NO_REFUND,
                confidence=0.95,
                reason="Customer claims double billing, but Stripe records confirm only one successful charge was billed. No duplicate charge exists.",
                supporting_evidence=r.refuting_evidence,
                risk_flags=["Financial ledger contradicts customer complaint"]
            )

        # Check for true duplicate (2+ charges found, no contradictions)
        if r.charges_found >= 2 and len(r.contradictions) == 0:
            return DecisionOutput(
                decision=DecisionType.REFUND_RECOMMENDED,
                confidence=0.94,
                reason="Two successful identical charges were found in Stripe with no refuting evidence across systems. Duplicate charge confirmed.",
                supporting_evidence=r.supporting_evidence,
                risk_flags=[]
            )

        # Default fallback
        return DecisionOutput(
            decision=DecisionType.ESCALATE_FOR_REVIEW,
            confidence=0.75,
            reason="Ambiguous evidence across systems requires human dispute specialist review.",
            supporting_evidence=r.supporting_evidence,
            risk_flags=r.risk_flags or ["Inconclusive cross-system proof"]
        )
