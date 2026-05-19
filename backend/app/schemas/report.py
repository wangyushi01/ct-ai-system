"""报告相关Schema"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.report import ReportStatus


class ReportBase(BaseModel):
    """报告基础Schema"""
    findings: str = Field(..., description="影像发现")
    impression: str = Field(..., description="诊断意见")
    recommendation: Optional[str] = None
    clinical_history: Optional[str] = None


class ReportCreate(ReportBase):
    """创建报告"""
    study_id: str = Field(..., description="检查ID")


class ReportUpdate(BaseModel):
    """更新报告"""
    findings: Optional[str] = None
    impression: Optional[str] = None
    recommendation: Optional[str] = None
    clinical_history: Optional[str] = None
    review_comment: Optional[str] = None


class Report(ReportBase):
    """报告响应"""
    id: str
    study_id: str
    radiologist_id: Optional[str] = None
    reviewer_id: Optional[str] = None

    report_type: str
    status: ReportStatus
    ai_generated: bool
    ai_confidence: Optional[float] = None

    review_comment: Optional[str] = None
    report_date: Optional[datetime] = None
    signed_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
