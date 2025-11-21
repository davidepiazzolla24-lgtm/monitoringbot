from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    healthy = "healthy"
    degraded = "degraded"
    down = "down"


class StatusResponse(BaseModel):
    service: str
    status: ServiceStatus
    updated_at: datetime
    details: Optional[str] = None


class TimelineEvent(BaseModel):
    id: str
    service: str
    level: str
    message: str
    timestamp: datetime


class Incident(BaseModel):
    id: str
    service: str
    summary: str
    impact: str
    opened_at: datetime
    closed_at: Optional[datetime] = None
    owner: Optional[str] = None


class Rule(BaseModel):
    id: str
    name: str
    expression: str
    severity: str
    enabled: bool = True
    description: Optional[str] = None


class CreateIncidentRequest(BaseModel):
    service: str = Field(..., description="Service involved")
    summary: str
    impact: str
    owner: Optional[str] = None


class CreateRuleRequest(BaseModel):
    name: str
    expression: str
    severity: str
    description: Optional[str] = None
    enabled: bool = True


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
