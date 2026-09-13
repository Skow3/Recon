from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database.db import get_db
from ..schemas.responses import EvaluationReport
from ..evaluation.runner import EvaluationRunner
from ..evaluation.scenarios import EVALUATION_SCENARIOS

router = APIRouter(prefix="/api", tags=["evaluation"])

@router.post("/evaluate", response_model=EvaluationReport)
def run_evaluation_suite(db: Session = Depends(get_db)):
    runner = EvaluationRunner(db)
    report = runner.run_all()
    return report

@router.get("/demo/scenarios", response_model=List[Dict[str, Any]])
def get_demo_scenarios():
    return EVALUATION_SCENARIOS
