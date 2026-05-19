"""检查相关API"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import json
from app.api.deps import get_db, get_current_user
from app.schemas.user import User
from app.schemas.study import (
    Patient, PatientCreate,
    Study, StudyCreate, StudyListResponse,
    Series, UploadProgress
)
from app.models.study import StudyStatus, ModalityType, BodyPart
from app.services.study_service import StudyService
from app.core.logger import logger

router = APIRouter()


@router.post("/patients", response_model=Patient, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建患者"""
    try:
        patient = await StudyService.create_patient(db, patient_data)
        return patient
    except Exception as e:
        logger.error(f"创建患者失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/patients", response_model=list[Patient])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取患者列表"""
    from sqlalchemy import select, or_
    from app.models.study import Patient

    query = select(Patient)

    if keyword:
        query = query.where(
            or_(
                Patient.name.contains(keyword),
                Patient.patient_id.contains(keyword),
                Patient.phone.contains(keyword)
            )
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    patients = result.scalars().all()

    return patients


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_study(
    study_data: StudyCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建检查"""
    try:
        # 从请求体获取完整数据
        import json
        body = await request.body()
        request_data = json.loads(body)

        # 创建患者数据
        patient_data = PatientCreate(
            patient_id=request_data.get('patient_id', ''),
            name=request_data.get('patient_name', '未知患者'),
            gender=request_data.get('gender', '男'),
            birth_date=datetime.strptime(request_data.get('birth_date', '1990-01-01'), '%Y-%m-%d').date(),
            phone=request_data.get('phone')
        )
        patient = await StudyService.create_patient(db, patient_data)

        # 创建检查
        study = await StudyService.create_study(db, study_data, patient)

        # 手动转换返回数据
        result_dict = {
            'id': str(study.id),
            'study_id': study.study_id,
            'patient_id': str(study.patient_id),
            'accession_number': study.accession_number,
            'study_date': study.study_date.isoformat() if study.study_date else None,
            'modality': study.modality.value if study.modality else None,
            'body_part': study.body_part.value if study.body_part else None,
            'study_description': study.study_description,
            'referring_physician': study.referring_physician,
            'status': study.status.value if study.status else None,
            'images_count': study.images_count,
            'file_size': study.file_size,
            'created_at': study.created_at.isoformat() if study.created_at else None,
            'updated_at': study.updated_at.isoformat() if study.updated_at else None,
            'patient': {
                'id': str(patient.id),
                'patient_id': patient.patient_id,
                'name': patient.name,
                'gender': patient.gender,
                'birth_date': patient.birth_date.isoformat() if patient.birth_date else None,
                'phone': patient.phone,
                'created_at': patient.created_at.isoformat() if patient.created_at else None,
            }
        }

        return result_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.get("", response_model=StudyListResponse)
async def list_studies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    patient_id: Optional[str] = None,
    modality: Optional[ModalityType] = None,
    body_part: Optional[BodyPart] = None,
    status: Optional[StudyStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取检查列表"""
    return await StudyService.list_studies(
        db,
        skip=skip,
        limit=limit,
        patient_id=patient_id,
        modality=modality,
        body_part=body_part,
        status=status
    )


@router.get("/{study_id}")
async def get_study(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取检查详情"""
    study = await StudyService.get_study_by_id(db, study_id)

    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检查不存在"
        )

    # 手动转换返回数据
    result_dict = {
        'id': str(study.id),
        'study_id': study.study_id,
        'patient_id': str(study.patient_id),
        'accession_number': study.accession_number,
        'study_date': study.study_date.isoformat() if study.study_date else None,
        'modality': study.modality.value if study.modality else None,
        'body_part': study.body_part.value if study.body_part else None,
        'study_description': study.study_description,
        'referring_physician': study.referring_physician,
        'status': study.status.value if study.status else None,
        'images_count': study.images_count,
        'file_size': study.file_size,
        'created_at': study.created_at.isoformat() if study.created_at else None,
        'updated_at': study.updated_at.isoformat() if study.updated_at else None,
    }

    # 处理patient关联
    if study.patient:
        result_dict['patient'] = {
            'id': str(study.patient.id),
            'patient_id': study.patient.patient_id,
            'name': study.patient.name,
            'gender': study.patient.gender,
            'birth_date': study.patient.birth_date.isoformat() if study.patient.birth_date else None,
            'phone': study.patient.phone,
            'created_at': study.patient.created_at.isoformat() if study.patient.created_at else None,
        }

    return result_dict


@router.delete("/{study_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_study(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除检查"""
    success = await StudyService.delete_study(db, study_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检查不存在"
        )


@router.get("/{study_id}/series", response_model=list[Series])
async def list_study_series(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取检查的系列列表"""
    from sqlalchemy import select
    from app.models.study import Series as SeriesModel, Study as StudyModel

    study_result = await db.execute(
        select(StudyModel).where(StudyModel.study_id == study_id)
    )
    study = study_result.scalar_one_or_none()

    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检查不存在"
        )

    result = await db.execute(
        select(SeriesModel).where(SeriesModel.study_id == study.id)
    )
    series = result.scalars().all()

    return series
