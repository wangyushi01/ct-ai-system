"""MinIO客户端"""
from minio import Minio
from app.core.config import settings
from app.core.logger import logger

minio_client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)

# 初始化时创建默认bucket
async def init_minio():
    """初始化MinIO存储桶"""
    try:
        buckets = ['ct-images', 'dicom-files']
        for bucket in buckets:
            if not minio_client.bucket_exists(bucket):
                minio_client.make_bucket(bucket)
                logger.info(f"创建MinIO桶: {bucket}")
    except Exception as e:
        logger.error(f"MinIO初始化失败: {e}")
