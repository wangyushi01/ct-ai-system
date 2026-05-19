"""检查服务"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid
from app.models.study import Patient, Study, Series, Image, StudyStatus
from app.schemas.study import PatientCreate, StudyCreate, StudyListResponse
from app.core.logger import logger


class StudyService:
    """检查服务"""

    @staticmethod
    async def create_patient(
        db: AsyncSession,
        patient_data: PatientCreate
    ) -> Patient:
        """创建患者"""
        # 检查患者ID是否已存在
        result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_data.patient_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        patient = Patient(**patient_data.model_dump())
        db.add(patient)
        await db.commit()
        await db.refresh(patient)

        logger.info(f"创建患者: {patient.patient_id}")
        return patient

    @staticmethod
    async def create_study(
        db: AsyncSession,
        study_data: StudyCreate,
        patient: Patient
    ) -> Study:
        """创建检查"""
        # 检查检查号是否已存在
        result = await db.execute(
            select(Study).where(Study.study_id == study_data.study_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"检查号 {study_data.study_id} 已存在")

        # 创建检查
        study_dict = study_data.model_dump()
        study_dict["patient_id"] = patient.id
        study_dict["status"] = StudyStatus.PENDING

        study = Study(**study_dict)
        db.add(study)
        await db.commit()
        await db.refresh(study)

        logger.info(f"创建检查: {study.study_id}")
        return study

    @staticmethod
    async def get_study_by_id(
        db: AsyncSession,
        study_id: str
    ) -> Optional[Study]:
        """根据ID获取检查（支持字符串检查号或UUID）"""
        from sqlalchemy import or_
        import uuid as _uuid

        # 先按字符串study_id查
        result = await db.execute(
            select(Study)
            .options(selectinload(Study.patient))
            .where(Study.study_id == study_id)
        )
        study = result.scalar_one_or_none()
        if study:
            return study

        # 如果是UUID格式，按主键查
        try:
            _uuid.UUID(study_id)
            result = await db.execute(
                select(Study)
                .options(selectinload(Study.patient))
                .where(Study.id == study_id)
            )
            return result.scalar_one_or_none()
        except ValueError:
            return None

    @staticmethod
    async def list_studies(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        patient_id: Optional[str] = None,
        modality: Optional[str] = None,
        body_part: Optional[str] = None,
        status: Optional[StudyStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        keyword: Optional[str] = None
    ) -> StudyListResponse:
        """获取检查列表"""
        query = select(Study).options(selectinload(Study.patient))

        # 构建过滤条件
        conditions = []

        if patient_id:
            conditions.append(Study.patient_id == patient_id)

        if modality:
            conditions.append(Study.modality == modality)

        if body_part:
            conditions.append(Study.body_part == body_part)

        if status:
            conditions.append(Study.status == status)

        if start_date:
            conditions.append(Study.study_date >= start_date)

        if end_date:
            conditions.append(Study.study_date <= end_date)

        if keyword:
            conditions.append(
                or_(
                    Study.study_id.contains(keyword),
                    Study.patient_id.contains(keyword),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # 按日期倒序
        query = query.order_by(Study.study_date.desc())

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        items = result.scalars().all()

        # 手动转换UUID为string
        converted_items = []
        for item in items:
            # 将ORM对象转换为dict
            item_dict = {
                'id': str(item.id),
                'study_id': item.study_id,
                'patient_id': str(item.patient_id),
                'accession_number': item.accession_number,
                'study_date': item.study_date.isoformat() if item.study_date else None,
                'modality': item.modality.value if item.modality else None,
                'body_part': item.body_part.value if item.body_part else None,
                'study_description': item.study_description,
                'referring_physician': item.referring_physician,
                'status': item.status.value if item.status else None,
                'images_count': item.images_count,
                'file_size': item.file_size,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'updated_at': item.updated_at.isoformat() if item.updated_at else None,
            }

            # 处理patient关联
            if hasattr(item, 'patient') and item.patient:
                item_dict['patient'] = {
                    'id': str(item.patient.id),
                    'patient_id': item.patient.patient_id,
                    'name': item.patient.name,
                    'gender': item.patient.gender,
                    'birth_date': item.patient.birth_date.isoformat() if item.patient.birth_date else None,
                    'phone': item.patient.phone,
                    'created_at': item.patient.created_at.isoformat() if item.patient.created_at else None,
                }

            converted_items.append(item_dict)

        return StudyListResponse(total=total, items=converted_items)

    @staticmethod
    async def update_study_status(
        db: AsyncSession,
        study_id: str,
        status: StudyStatus
    ) -> Optional[Study]:
        """更新检查状态"""
        result = await db.execute(
            select(Study).where(Study.study_id == study_id)
        )
        study = result.scalar_one_or_none()

        if study:
            study.status = status
            await db.commit()
            await db.refresh(study)
            logger.info(f"更新检查状态: {study_id} -> {status}")

        return study

    @staticmethod
    async def update_study_images(
        db: AsyncSession,
        study_id: str,
        images_count: int,
        file_size: float
    ) -> Optional[Study]:
        """更新检查影像信息"""
        result = await db.execute(
            select(Study).where(Study.study_id == study_id)
        )
        study = result.scalar_one_or_none()

        if study:
            study.images_count = images_count
            study.file_size = file_size
            await db.commit()
            await db.refresh(study)

        return study

    @staticmethod
    async def delete_study(db: AsyncSession, study_id: str) -> bool:
        """删除检查"""
        from app.models.analysis import AnalysisTask, Detection
        from app.models.report import Report

        result = await db.execute(
            select(Study).where(Study.study_id == study_id)
        )
        study = result.scalar_one_or_none()

        if study:
            # 先获取所有相关的分析任务ID
            task_result = await db.execute(
                select(AnalysisTask.id).where(AnalysisTask.study_id == study.id)
            )
            task_ids = [t[0] for t in task_result.all()]

            # 删除关联的检测结果
            if task_ids:
                await db.execute(
                    delete(Detection).where(Detection.task_id.in_(task_ids))
                )

            # 删除关联的分析任务
            await db.execute(
                delete(AnalysisTask).where(AnalysisTask.study_id == study.id)
            )

            # 删除关联的报告
            await db.execute(
                delete(Report).where(Report.study_id == study.id)
            )

            # 获取所有系列ID
            series_result = await db.execute(
                select(Series.id).where(Series.study_id == study.id)
            )
            series_ids = [s[0] for s in series_result.all()]

            # 删除系列下的影像
            if series_ids:
                await db.execute(
                    delete(Image).where(Image.series_id.in_(series_ids))
                )

            # 删除系列
            await db.execute(
                delete(Series).where(Series.study_id == study.id)
            )

            # 删除检查
            await db.execute(
                delete(Study).where(Study.study_id == study_id)
            )
            await db.commit()
            logger.info(f"删除检查: {study_id}")
            return True

        return False
