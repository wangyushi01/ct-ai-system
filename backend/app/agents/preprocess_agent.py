"""预处理Agent - 负责CT影像预处理"""
import numpy as np
from typing import Any, Dict, List
from app.agents.base import BaseAgent
from app.ml.preprocessing import preprocess_pipeline, get_window_for_body_part
from app.ml.utils import load_dicom_from_minio
from app.core.logger import logger


class PreprocessAgent(BaseAgent):
    """影像预处理Agent"""

    def __init__(self):
        super().__init__("PreprocessAgent", "负责CT影像预处理，包括去噪、标准化、窗宽窗位调整等")

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行预处理流水线
        输入: { study_id, body_part }
        输出: { images: [...], total_count, body_part }
        """
        study_id = input_data.get("study_id")
        body_part = input_data.get("body_part", "CHEST")

        logger.info(f"PreprocessAgent: 开始预处理检查 {study_id}")

        # 从MinIO加载DICOM影像
        raw_images = await load_dicom_from_minio(study_id)

        if not raw_images:
            raise ValueError(f"检查 {study_id} 无法读取影像数据")

        # 预处理每张影像
        processed_images = []
        for img_data in raw_images[:50]:  # 最多处理50张
            pixel_array = img_data["pixel_data"]
            processed = preprocess_pipeline(pixel_array, body_part)

            processed_images.append({
                "pixel_data": processed,
                "series_id": img_data["series_id"],
                "sop_instance_uid": img_data["sop_instance_uid"],
                "image_number": img_data["image_number"],
            })

        window = get_window_for_body_part(body_part)

        result = {
            "images": processed_images,
            "total_count": len(processed_images),
            "body_part": body_part,
            "window": window,
            "study_id": study_id,
        }

        logger.info(f"PreprocessAgent: 预处理完成，共 {len(processed_images)} 张影像")
        return result
