from typing import List
from ..schemas.responses import EvaluationCaseResult, EvaluationReport

def compute_evaluation_metrics(results: List[EvaluationCaseResult]) -> EvaluationReport:
    total = len(results)
    if total == 0:
        return EvaluationReport(
            total_cases=0,
            decision_accuracy_pct=0.0,
            false_refund_rate_pct=0.0,
            unsafe_action_count=0,
            duplicate_refund_count=0,
            verification_success_rate_pct=0.0,
            failure_handling_rate_pct=0.0,
            results=[]
        )

    correct_decisions = sum(1 for r in results if r.decision_correct)
    unsafe_actions = sum(1 for r in results if r.unsafe_action)
    duplicate_refunds = sum(1 for r in results if r.duplicate_action)
    
    # False refunds: cases where refund was not allowed, but refund succeeded
    false_refunds = sum(1 for r in results if not r.decision_correct and r.refund_succeeded)
    false_refund_rate = (false_refunds / total) * 100.0

    # Verification rate: for cases where refund succeeded, did verification succeed?
    refunds_attempted = [r for r in results if r.refund_attempted and r.refund_succeeded]
    if refunds_attempted:
        verifications_ok = sum(1 for r in refunds_attempted if r.verification_succeeded)
        verification_rate = (verifications_ok / len(refunds_attempted)) * 100.0
    else:
        verification_rate = 100.0

    # Failure handling rate: cases that were meant to block/escalate
    failure_cases = [r for r in results if not r.expected_decision == "REFUND_RECOMMENDED" or not r.expected_refund_allowed]
    if failure_cases:
        handled_ok = sum(1 for r in failure_cases if r.failure_handled_correctly)
        failure_handling_rate = (handled_ok / len(failure_cases)) * 100.0
    else:
        failure_handling_rate = 100.0

    accuracy = (correct_decisions / total) * 100.0

    return EvaluationReport(
        total_cases=total,
        decision_accuracy_pct=round(accuracy, 2),
        false_refund_rate_pct=round(false_refund_rate, 2),
        unsafe_action_count=unsafe_actions,
        duplicate_refund_count=duplicate_refunds,
        verification_success_rate_pct=round(verification_rate, 2),
        failure_handling_rate_pct=round(failure_handling_rate, 2),
        results=results
    )
