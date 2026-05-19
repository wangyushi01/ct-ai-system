"""ML工具函数"""
import numpy as np
from typing import Dict, List, Any


async def load_dicom_from_minio(study_id: str) -> List[Dict[str, Any]]:
    """从MinIO加载DICOM影像数据（异步）"""
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.study import Study, Series, Image
    from app.core.config import settings
    from minio import Minio
    import pydicom
    from io import BytesIO
    from app.core.logger import logger

    images_data = []

    async with AsyncSessionLocal() as db:
        study_result = await db.execute(
            select(Study).where(Study.study_id == study_id)
        )
        study = study_result.scalar_one_or_none()
        if not study or study.images_count == 0:
            return images_data

        series_result = await db.execute(
            select(Series).where(Series.study_id == study.id)
        )
        series_list = series_result.scalars().all()

        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

        for series in series_list:
            images_result = await db.execute(
                select(Image).where(Image.series_id == series.id)
            )
            images = images_result.scalars().all()

            for img_record in images:
                try:
                    file_path = img_record.file_path.lstrip("/")
                    # 去掉可能包含的桶名前缀
                    if file_path.startswith("ct-images/"):
                        file_path = file_path[len("ct-images/"):]
                    data = minio_client.get_object("ct-images", file_path)
                    dcm = pydicom.read_file(BytesIO(data.read()))
                    pixel_array = dcm.pixel_array.astype(np.float32)

                    images_data.append({
                        "pixel_data": pixel_array,
                        "series_id": series.series_id,
                        "sop_instance_uid": img_record.sop_instance_uid,
                        "image_number": img_record.image_number,
                    })
                except Exception as e:
                    logger.error(f"读取影像失败 {img_record.sop_instance_uid}: {e}")

    return images_data


def classify_lesion_type(diameter: float, mean_intensity: float) -> str:
    """基于特征判断病灶类型"""
    if diameter < 20 and mean_intensity < 0.1:
        return "肝囊肿"
    elif diameter < 50 and 0.1 < mean_intensity < 0.3:
        return "肝血管瘤"
    elif diameter > 20:
        return "占位性病变"
    else:
        return "低密度灶"
