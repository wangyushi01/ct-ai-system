"""分析相关Schema"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.analysis import AnalysisType, TaskStatus


class AnalysisCreate(BaseModel):
    """创建分析任务"""
    study_id: str = Field(..., description="检查ID")
    task_type: AnalysisType = Field(..., description="分析类型")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")


class DetectionItem(BaseModel):
    """检测项"""
    id: Any
    label: str
    confidence: float
    location: Dict[str, float]  # {x, y, z}
    size: Optional[Dict[str, float]] = None  # {diameter, volume}
    properties: Optional[Dict[str, Any]] = None  # {shape, margin, density}

    @field_serializer('id')
    def serialize_id(self, value: Any) -> str:
        return str(value)


class AnalysisTaskResponse(BaseModel):
    """分析任务响应"""
    id: Any
    study_id: Any
    task_type: AnalysisType
    status: TaskStatus
    priority: int
    progress: float
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    # 检测结果
    detections: List[DetectionItem] = []

    @field_serializer('id', 'study_id')
    def serialize_ids(self, value: Any) -> str:
        return str(value)

    class Config:
        from_attributes = True


class DiagnosisResult(BaseModel):
    """诊断结果"""
    primary_diagnosis: str
    differential_diagnosis: List[Dict[str, Any]]
    probability: float
    risk_level: str
    recommendations: List[str]


class AnalysisResponse(BaseModel):
    """分析响应"""
    task: AnalysisTaskResponse
    diagnosis: Optional[DiagnosisResult] = None
