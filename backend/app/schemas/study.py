"""检查相关Schema"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Any
from datetime import datetime, date
from uuid import UUID
from app.models.study import ModalityType, BodyPart, StudyStatus


class PatientBase(BaseModel):
    """患者基础Schema"""
    patient_id: str = Field(..., description="患者ID")
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., pattern="^(男|女)$")
    birth_date: date
    phone: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    id_card: Optional[str] = None
    address: Optional[str] = None


class PatientCreate(PatientBase):
    """创建患者"""
    pass


class Patient(PatientBase):
    """患者响应"""
    id: Any
    created_at: datetime

    @field_serializer('id')
    def serialize_id(self, value: Any) -> str:
        return str(value)

    class Config:
        from_attributes = True


class StudyBase(BaseModel):
    """检查基础Schema"""
    study_id: str = Field(..., description="检查号")
    patient_id: Any = Field(..., description="患者ID")
    accession_number: Optional[str] = None
    study_date: datetime
    modality: ModalityType
    body_part: BodyPart
    study_description: Optional[str] = None
    referring_physician: Optional[str] = None

    @field_serializer('patient_id')
    def serialize_patient_id(self, value: Any) -> str:
        return str(value)


class StudyCreate(StudyBase):
    """创建检查"""
    pass


class Study(StudyBase):
    """检查响应"""
    id: Any
    status: StudyStatus
    images_count: int
    file_size: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    # 关联数据
    patient: Optional[Patient] = None

    @field_serializer('id')
    def serialize_id(self, value: Any) -> str:
        return str(value)

    class Config:
        from_attributes = True


class StudyListResponse(BaseModel):
    """检查列表响应"""
    total: int
    items: List[Any]


class SeriesBase(BaseModel):
    """系列基础Schema"""
    series_id: str
    series_number: int
    modality: str
    series_description: Optional[str] = None
    body_part_examined: Optional[str] = None
    images_count: int = 0


class Series(SeriesBase):
    """系列响应"""
    id: Any
    study_id: str
    created_at: datetime

    @field_serializer('id', 'study_id')
    def serialize_ids(self, value: Any) -> str:
        return str(value)

    class Config:
        from_attributes = True


class ImageInfo(BaseModel):
    """影像信息"""
    id: Any
    sop_instance_uid: str
    image_number: int
    file_path: str
    rows: Optional[int] = None
    columns: Optional[int] = None

    @field_serializer('id')
    def serialize_id(self, value: Any) -> str:
        return str(value)


class UploadProgress(BaseModel):
    """上传进度"""
    study_id: str
    status: str
    uploaded_count: int
    total_count: int
    progress: float
