"""数据库初始化脚本"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import init_db, close_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.core.logger import logger


async def create_admin_user():
    """创建管理员用户"""
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # 检查管理员是否已存在
        result = await db.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()

        if admin:
            logger.info("管理员用户已存在")
            return admin

        # 创建管理员
        admin = User(
            username="admin",
            email="admin@ct-ai.com",
            hashed_password=get_password_hash("admin123"),
            full_name="系统管理员",
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        logger.info("管理员用户创建成功")
        return admin


async def create_demo_users():
    """创建演示用户"""
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # 检查演示用户是否已存在
        result = await db.execute(
            select(User).where(User.username == "radiologist1")
        )
        if result.scalar_one_or_none():
            logger.info("演示用户已存在")
            return

        # 创建放射科医生
        radiologist = User(
            username="radiologist1",
            email="radiologist1@ct-ai.com",
            hashed_password=get_password_hash("demo123"),
            full_name="张医生",
            role=UserRole.RADIOLOGIST,
            department="放射科",
            is_active=True,
        )
        db.add(radiologist)

        # 创建临床医生
        clinician = User(
            username="clinician1",
            email="clinician1@ct-ai.com",
            hashed_password=get_password_hash("demo123"),
            full_name="李医生",
            role=UserRole.CLINICIAN,
            department="内科",
            is_active=True,
        )
        db.add(clinician)

        await db.commit()
        logger.info("演示用户创建成功")


async def create_demo_studies():
    """创建演示检查数据"""
    from datetime import datetime, timedelta
    import uuid
    from app.db.session import AsyncSessionLocal
    from app.models.study import Patient, Study, ModalityType, BodyPart, StudyStatus

    async with AsyncSessionLocal() as db:
        # 创建演示患者
        patients_data = [
            {
                "patient_id": "P2024001",
                "name": "王先生",
                "gender": "男",
                "birth_date": datetime(1965, 5, 15).date(),
                "phone": "138****1234",
            },
            {
                "patient_id": "P2024002",
                "name": "张女士",
                "gender": "女",
                "birth_date": datetime(1970, 8, 22).date(),
                "phone": "139****5678",
            },
            {
                "patient_id": "P2024003",
                "name": "李先生",
                "gender": "男",
                "birth_date": datetime(1958, 3, 10).date(),
                "phone": "136****9012",
            },
        ]

        for patient_data in patients_data:
            result = await db.execute(
                select(Patient).where(Patient.patient_id == patient_data["patient_id"])
            )
            if result.scalar_one_or_none():
                continue

            patient = Patient(**patient_data)
            db.add(patient)

        await db.commit()
        logger.info("演示患者创建成功")

        # 创建演示检查
        studies_mapping = [
            {
                "study_id": "ST2024001",
                "patient_id_str": "P2024001",
                "accession_number": "ACC2024001",
                "study_date": datetime.now() - timedelta(days=2),
                "modality": ModalityType.CT,
                "body_part": BodyPart.CHEST,
                "study_description": "胸部CT平扫",
                "status": StudyStatus.COMPLETED,
                "images_count": 120,
                "file_size": 45.5,
            },
            {
                "study_id": "ST2024002",
                "patient_id_str": "P2024002",
                "accession_number": "ACC2024002",
                "study_date": datetime.now() - timedelta(days=1),
                "modality": ModalityType.CT,
                "body_part": BodyPart.HEAD,
                "study_description": "头颅CT平扫",
                "status": StudyStatus.ANALYZING,
                "images_count": 80,
                "file_size": 30.2,
            },
            {
                "study_id": "ST2024003",
                "patient_id_str": "P2024003",
                "accession_number": "ACC2024003",
                "study_date": datetime.now(),
                "modality": ModalityType.CT,
                "body_part": BodyPart.ABDOMEN,
                "study_description": "腹部CT增强扫描",
                "status": StudyStatus.PENDING,
                "images_count": 150,
                "file_size": 60.8,
            },
        ]

        for study_data in studies_mapping:
            result = await db.execute(
                select(Study).where(Study.study_id == study_data["study_id"])
            )
            if result.scalar_one_or_none():
                continue

            # 获取患者
            patient_result = await db.execute(
                select(Patient).where(Patient.patient_id == study_data["patient_id_str"])
            )
            patient = patient_result.scalar_one_or_none()

            if not patient:
                continue

            # 创建Study对象，使用UUID patient_id
            study = Study(
                study_id=study_data["study_id"],
                patient_id=patient.id,
                accession_number=study_data["accession_number"],
                study_date=study_data["study_date"],
                modality=study_data["modality"],
                body_part=study_data["body_part"],
                study_description=study_data["study_description"],
                status=study_data["status"],
                images_count=study_data["images_count"],
                file_size=study_data["file_size"],
            )
            db.add(study)

        await db.commit()
        logger.info("演示检查创建成功")


async def main():
    """主函数"""
    logger.info("开始初始化数据库...")

    try:
        # 初始化数据库表
        await init_db()

        # 创建管理员用户
        await create_admin_user()

        # 创建演示用户
        await create_demo_users()

        # 创建演示数据（已注释，由用户手动添加）
        # await create_demo_studies()

        logger.info("数据库初始化完成")

        print("\n" + "=" * 50)
        print("数据库初始化成功！")
        print("=" * 50)
        print("\n默认账号：")
        print("  管理员：admin / admin123")
        print("\n")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
