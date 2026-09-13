from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ActionType(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    FINANCIAL = "FINANCIAL"
    COMMUNICATION = "COMMUNICATION"

class ToolDefinition(BaseModel):
    name: str
    app_id: str
    display_name: str
    description: str
    action_type: ActionType
    requires_approval: bool = False
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)

class AppCategory(str, Enum):
    COMMUNICATION = "Communication"
    PAYMENTS = "Finance & Payments"
    PRODUCTIVITY = "Productivity & Docs"
    DEVELOPER = "Developer & Code"
    PROJECT = "Project Management"

class AppMetadata(BaseModel):
    app_id: str
    name: str
    category: AppCategory
    description: str
    icon: str
    status: str = "available" # "connected", "available", "coming_soon"
    supported_events: List[str] = Field(default_factory=list)
    available_actions: List[str] = Field(default_factory=list)
