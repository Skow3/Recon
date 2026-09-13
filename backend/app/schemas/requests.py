from typing import Optional
from pydantic import BaseModel, Field

class CaseCreateRequest(BaseModel):
    user_request: str = Field(..., description="Customer dispute complaint or inquiry description")
    customer_name: Optional[str] = Field(default=None, description="Customer or business name")
    customer_email: Optional[str] = Field(default=None, description="Customer email address")
    scenario_id: Optional[str] = Field(default=None, description="Pre-configured mock scenario ID if applicable")

class ApprovalRequest(BaseModel):
    approved: bool = Field(..., description="True to approve the recommended refund; False to reject")
    approved_by: str = Field(default="human", description="User or role executing the approval")
    notes: Optional[str] = Field(default=None, description="Optional notes regarding the approval decision")
