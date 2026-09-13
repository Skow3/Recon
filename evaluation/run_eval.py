import os
import sys
from pathlib import Path

# Add backend to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.evaluation.runner import run_evaluation

if __name__ == "__main__":
    report = run_evaluation()
    print("=" * 60)
    print("RECON RELIABILITY & EVALUATION REPORT")
    print("=" * 60)
    print(f"Total Test Cases:           {report.total_cases}")
    print(f"Decision Accuracy:          {report.decision_accuracy_pct}%")
    print(f"False Refund Rate:          {report.false_refund_rate_pct}%")
    print(f"Unsafe Action Count:        {report.unsafe_action_count}")
    print(f"Duplicate Refund Count:     {report.duplicate_refund_count}")
    print(f"Verification Success Rate:  {report.verification_success_rate_pct}%")
    print(f"Failure Handling Rate:      {report.failure_handling_rate_pct}%")
    print("=" * 60)
    for idx, r in enumerate(report.results, 1):
        status_sym = "✓ PASS" if r.decision_correct and not r.unsafe_action and not r.duplicate_action else "✗ FAIL"
        print(f"[{status_sym}] #{idx}: {r.case_name}")
        print(f"       Decision: Expected {r.expected_decision} | Actual: {r.actual_decision}")
        print(f"       Outcome:  State={r.final_state} | Notes: {r.notes}")
    print("=" * 60)
    if report.unsafe_action_count == 0 and report.false_refund_rate_pct == 0.0:
        print("ALL SAFETY GUARANTEES VERIFIED: 0 UNSAFE ACTIONS, 0 FALSE REFUNDS.")
    print("=" * 60)
