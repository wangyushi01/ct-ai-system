"""文件上传API"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
import uuid
from io import BytesIO
import pydicom

from app.api.deps import get_db, get_current_user
from app.schemas.user import User
from app.models.study import Study, Series, Image, StudyStatus
from app.core.logger import logger
from app.core.minio_client import minio_client

router = APIRouter()


@router.post("/studies/{study_id}/upload", status_code=status.HTTP_201_CREATED)
async def upload_dicom(
    study_id: str,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传DICOM文件到指定检查
    支持批量上传多个DICOM文件
    """
    # 验证检查是否存在
    result = await db.execute(
        select(Study).where(Study.study_id == study_id)
    )
    study = result.scalar_one_or_none()

    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检查不存在"
        )

    uploaded_count = 0
    errors = []

    for file in files:
        try:
            content = await file.read()

            # 尝试解析DICOM文件
            try:
                dcm = pydicom.read_file(BytesIO(content))
            except Exception as e:
                # 非DICOM文件也允许上传（普通图片等），作为普通文件存储
                errors.append(f"{file.filename}: 非标准DICOM文件，已跳过 - {str(e)}")
                continue

            # 提取DICOM标签
            series_uid = str(dcm.get('SeriesInstanceUID', str(uuid.uuid4())))
            sop_uid = str(dcm.get('SOPInstanceUID', str(uuid.uuid4())))
            series_number = int(dcm.get('SeriesNumber', 1) or 1)
            instance_number = int(dcm.get('InstanceNumber', 1) or 1)
            modality = str(dcm.get('Modality', 'CT') or 'CT')

            # 查找或创建系列（按series_number匹配）
            series_result = await db.execute(
                select(Series).where(
                    Series.study_id == study.id,
                    Series.series_number == series_number
                )
            )
            series = series_result.scalar_one_or_none()

            if not series:
                series = Series(
                    study_id=study.id,
                    series_id=f"SER_{uuid.uuid4().hex[:8]}",
                    series_number=series_number,
                    modality=modality,
                    series_description=str(dcm.get('SeriesDescription', '') or ''),
                    body_part_examined=str(dcm.get('BodyPartExamined', '') or ''),
                    images_count=0
                )
                db.add(series)
                await db.flush()

            # 检查影像是否已存在
            image_result = await db.execute(
                select(Image).where(Image.sop_instance_uid == sop_uid)
            )
            if image_result.scalar_one_or_none():
                continue

            # 上传到MinIO
            bucket_name = "ct-images"
            object_name = f"{study_id}/{series.series_id}/{sop_uid}.dcm"

            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)

            minio_client.put_object(
                bucket_name,
                object_name,
                data=BytesIO(content),
                length=len(content),
                content_type='application/dicom'
            )

            # 创建影像记录
            image = Image(
                sop_instance_uid=sop_uid,
                series_id=series.id,
                image_number=instance_number,
                instance_number=instance_number,
                file_path=f"{bucket_name}/{object_name}",
                file_size=len(content),
                rows=int(dcm.get('Rows', 512) or 512),
                columns=int(dcm.get('Columns', 512) or 512)
            )
            db.add(image)

            series.images_count += 1
            uploaded_count += 1
            logger.info(f"上传成功: {file.filename}")

        except Exception as e:
            logger.error(f"上传失败 {file.filename}: {e}")
            errors.append(f"{file.filename}: {str(e)}")

    # 更新检查的影像数量
    series_list_result = await db.execute(
        select(Series).where(Series.study_id == study.id)
    )
    series_list = series_list_result.scalars().all()

    total_images = sum(s.images_count for s in series_list)
    study.images_count = total_images

    if total_images > 0:
        study.status = StudyStatus.PROCESSING

    await db.commit()

    return {
        "success": True,
        "uploaded_count": uploaded_count,
        "total_images": total_images,
        "errors": errors
    }


@router.get("/studies/{study_id}/upload-status")
async def get_upload_status(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取上传状态"""
    result = await db.execute(
        select(Study).where(Study.study_id == study_id)
    )
    study = result.scalar_one_or_none()

    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检查不存在"
        )

    series_result = await db.execute(
        select(Series).where(Series.study_id == study.id)
    )
    series_list = series_result.scalars().all()

    return {
        "study_id": study.study_id,
        "images_count": study.images_count,
        "series_count": len(series_list),
        "status": study.status.value if study.status else None,
        "series": [
            {
                "series_number": s.series_number,
                "series_description": s.series_description,
                "images_count": s.images_count
            }
            for s in series_list
        ]
    }


@router.delete("/studies/{study_id}/images", status_code=status.HTTP_200_OK)
async def delete_study_images(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除检查的所有影像"""
    result = await db.execute(
        select(Study).where(Study.study_id == study_id)
    )
    study = result.scalar_one_or_none()

    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检查不存在"
        )

    # 获取所有系列
    series_result = await db.execute(
        select(Series).where(Series.study_id == study.id)
    )
    series_list = series_result.scalars().all()

    # 删除所有影像记录
    for series in series_list:
        await db.execute(delete(Image).where(Image.series_id == series.id))

    # 删除所有系列记录
    await db.execute(delete(Series).where(Series.study_id == study.id))

    # 更新检查信息
    study.images_count = 0
    study.file_size = None
    study.status = StudyStatus.PENDING

    await db.commit()

    logger.info(f"删除检查影像: {study_id}")
    return {"success": True, "message": "影像已全部删除"}


@router.get("/studies/{study_id}/images")
async def list_study_images(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取检查的所有影像列表"""
    result = await db.execute(
        select(Study).where(Study.study_id == study_id)
    )
    study = result.scalar_one_or_none()

    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检查不存在"
        )

    # 获取所有系列及其影像
    series_result = await db.execute(
        select(Series).where(Series.study_id == study.id)
    )
    series_list = series_result.scalars().all()

    result_data = []
    for series in series_list:
        images_result = await db.execute(
            select(Image).where(Image.series_id == series.id)
        )
        images = images_result.scalars().all()

        result_data.append({
            "series_id": str(series.id),
            "series_number": series.series_number,
            "series_description": series.series_description,
            "modality": series.modality,
            "images_count": series.images_count,
            "images": [
                {
                    "id": str(img.id),
                    "sop_instance_uid": img.sop_instance_uid,
                    "image_number": img.image_number,
                    "file_size": img.file_size,
                    "rows": img.rows,
                    "columns": img.columns,
                }
                for img in images
            ]
        })

    return {
        "study_id": study_id,
        "total_images": study.images_count,
        "series": result_data
    }
