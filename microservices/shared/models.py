"""Shared Pydantic models across microservices"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Agent Models
class AgentBase(BaseModel):
    name: str
    model: str
    role: Optional[str] = ""
    goal: Optional[str] = ""
    instructions: Optional[str] = ""

class AgentCreate(AgentBase):
    user_id: Optional[str] = "default"
    enable_memory: bool = False

class AgentResponse(AgentBase):
    id: str
    user_id: str
    status: str
    created_at: str

# Task Models
class TaskBase(BaseModel):
    description: str

class TaskCreate(TaskBase):
    agent_id: str

class TaskResponse(TaskBase):
    id: str
    agent_id: str
    result: Optional[str] = None
    status: str
    execution_time_ms: Optional[float] = None
    created_at: str
    completed_at: Optional[str] = None

# Memory Models
class SessionBase(BaseModel):
    session_id: str

class SessionCreate(SessionBase):
    storage_type: str = "memory"

class SessionResponse(SessionBase):
    storage_type: str
    created_at: str

class MessageCreate(BaseModel):
    session_id: str
    role: str
    content: str

# Health Check
class HealthResponse(BaseModel):
    service: str
    status: str
    version: str
    timestamp: str

# Risk Scoring Models
class CompanyInfo(BaseModel):
    company_type: str
    merchant_name: str
    trade_name: str
    mersis_number: Optional[str] = None
    language: str = "TR"
    monthly_revenue: Optional[float] = None
    sales_representative: Optional[str] = None
    mcc_code: Optional[str] = None
    hosting_vkn: Optional[str] = None
    hosting_url: Optional[str] = None
    country: str = "TR"
    city: str
    district: str
    postal_code: Optional[str] = None
    address: str
    application_channel: Optional[str] = None
    integrator_condition: Optional[str] = None
    contract_date: Optional[str] = None
    merchant_number: Optional[str] = None
    hosting_title: Optional[str] = None
    bkm_number: Optional[str] = None

class AuthorizedPersonInfo(BaseModel):
    tc_number: str
    first_name: str
    last_name: str
    email: str
    company_email: Optional[str] = None
    birth_date: Optional[str] = None
    mobile_phone: str

class DocumentInfo(BaseModel):
    contract: Optional[str] = None
    iban_receipt: Optional[str] = None
    findeks_report: Optional[str] = None
    tax_plate: Optional[str] = None
    activity_info: Optional[str] = None
    identity_info: Optional[str] = None
    signature_circular: Optional[str] = None
    trade_registry: Optional[str] = None

class MerchantApplication(BaseModel):
    company_info: CompanyInfo
    authorized_person: AuthorizedPersonInfo
    documents: DocumentInfo

class RiskScoreRequest(BaseModel):
    application: MerchantApplication

class RiskScoreSource(BaseModel):
    source_name: str
    source_url: Optional[str] = None
    data_found: str
    risk_impact: str
    score_contribution: float

class RiskScoreResponse(BaseModel):
    application_id: str
    merchant_name: str
    total_risk_score: float  # 0-100, higher is better
    risk_category: str  # LOW, MEDIUM, HIGH, CRITICAL
    sources: List[RiskScoreSource]
    summary: str
    recommendations: List[str]
    created_at: str
    processed_by: str

class EmailRecipient(BaseModel):
    department: str  # Risk, Uyum, Operasyon, Fraud, Product
    email: str

class ReportRequest(BaseModel):
    risk_score_id: str
    recipients: List[EmailRecipient]
