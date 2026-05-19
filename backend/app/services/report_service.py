"""报告服务"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime
from app.models.report import Report, ReportStatus
from app.models.study import Study, StudyStatus
from app.models.analysis import AnalysisTask, Detection
from app.schemas.report import ReportCreate, ReportUpdate
from app.core.logger import logger


class ReportService:
    """报告服务"""

    @staticmethod
    async def create_report(
        db: AsyncSession,
        study_id: str,
        report_data: ReportCreate,
        radiologist_id: str,
        ai_generated: bool = False
    ) -> Report:
        """创建报告"""
        # 获取检查
        result = await db.execute(
            select(Study).where(Study.study_id == study_id)
        )
        study = result.scalar_one_or_none()

        if not study:
            raise ValueError(f"检查 {study_id} 不存在")

        # 检查是否已有报告
        existing = await db.execute(
            select(Report).where(Report.study_id == study.id)
        )
        existing_report = existing.scalar_one_or_none()

        if existing_report:
            raise ValueError("该检查已有报告，请使用更新接口")

        # 创建报告
        report = Report(
            study_id=study.id,
            radiologist_id=radiologist_id,
            findings=report_data.findings,
            impression=report_data.impression,
            recommendation=report_data.recommendation,
            clinical_history=report_data.clinical_history,
            status=ReportStatus.DRAFT,
            ai_generated=ai_generated,
            report_date=datetime.utcnow()
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        # 更新检查状态
        study.status = StudyStatus.REPORTED
        await db.commit()

        logger.info(f"创建报告: {report.id} for study {study_id}")
        return report

    @staticmethod
    async def generate_ai_report(
        db: AsyncSession,
        study_id: str,
        radiologist_id: str
    ) -> Report:
        """基于AI分析生成报告"""
        # 获取检查
        result = await db.execute(
            select(Study)
            .options(selectinload(Study.patient))
            .where(Study.study_id == study_id)
        )
        study = result.scalar_one_or_none()

        if not study:
            raise ValueError(f"检查 {study_id} 不存在")

        from app.models.analysis import TaskStatus

        # 获取最新的AI分析结果
        result = await db.execute(
            select(AnalysisTask)
            .where(AnalysisTask.study_id == study.id)
            .where(AnalysisTask.status == TaskStatus.COMPLETED)
            .order_by(desc(AnalysisTask.created_at))
            .limit(1)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError("该检查暂无AI分析结果")

        # 获取检测结果
        detections_result = await db.execute(
            select(Detection).where(Detection.task_id == str(task.id))
        )
        detections = detections_result.scalars().all()

        # 生成报告内容
        findings = await ReportService._generate_findings(study, detections, task)
        impression = await ReportService._generate_impression(detections, task)
        recommendation = await ReportService._generate_recommendation(detections)

        # 创建报告
        report_data = ReportCreate(
            study_id=study_id,
            findings=findings,
            impression=impression,
            recommendation=recommendation,
            clinical_history=f"患者{study.patient.name}（{study.patient.gender}，{study.patient.birth_date.strftime('%Y-%m-%d')}）于{study.study_date.strftime('%Y-%m-%d')}行{study.modality}检查。"
        )

        return await ReportService.create_report(
            db,
            study_id,
            report_data,
            radiologist_id,
            ai_generated=True
        )

    @staticmethod
    async def _generate_findings(
        study: Study,
        detections: List[Detection],
        task: AnalysisTask
    ) -> str:
        """生成影像发现"""
        findings_parts = []

        # 检查类型和部位
        findings_parts.append(f"检查类型：{study.modality.value}，检查部位：{study.body_part.value}。")
        findings_parts.append(f"影像数量：{study.images_count}张。")

        if not detections:
            findings_parts.append("\n影像表现：未见明显异常。")
        else:
            findings_parts.append(f"\n影像表现：发现{len(detections)}个异常病灶。")

            for i, det in enumerate(detections, 1):
                det_info = f"\n{i}. {det.label}（置信度：{det.confidence:.2%}）"

                # 位置信息
                if det.location:
                    loc_parts = []
                    if 'region' in det.location:
                        loc_parts.append(det.location['region'])
                    if 'side' in det.location:
                        loc_parts.append(det.location['side'])
                    if 'x' in det.location:
                        loc_parts.append(f"X:{det.location['x']:.1f}mm")
                    if 'y' in det.location:
                        loc_parts.append(f"Y:{det.location['y']:.1f}mm")
                    if 'z' in det.location:
                        loc_parts.append(f"Z:{det.location['z']:.1f}mm")

                    if loc_parts:
                        det_info += f"\n   位置：{' '.join(loc_parts)}"

                # 大小信息
                if det.size:
                    size_parts = []
                    if 'diameter' in det.size:
                        size_parts.append(f"直径{det.size['diameter']:.1f}mm")
                    if 'volume' in det.size:
                        size_parts.append(f"体积{det.size['volume']:.1f}mm³")

                    if size_parts:
                        det_info += f"\n   大小：{', '.join(size_parts)}"

                # 属性信息
                if det.properties:
                    prop_parts = []
                    for key, value in det.properties.items():
                        prop_parts.append(f"{key}：{value}")

                    if prop_parts:
                        det_info += f"\n   特征：{', '.join(prop_parts)}"

                findings_parts.append(det_info)

        return "\n".join(findings_parts)

    @staticmethod
    async def _generate_impression(
        detections: List[Detection],
        task: AnalysisTask
    ) -> str:
        """生成诊断意见"""
        if not detections:
            return "影像学表现未见明显异常。"

        # 按置信度排序
        sorted_detections = sorted(detections, key=lambda x: x.confidence, reverse=True)

        impression_parts = []

        # 主要诊断
        main_detection = sorted_detections[0]
        impression_parts.append(f"1. {main_detection.label}（置信度：{main_detection.confidence:.2%}）")

        # 其他发现
        if len(sorted_detections) > 1:
            for det in sorted_detections[1:]:
                impression_parts.append(f"2. {det.label}（置信度：{det.confidence:.2%}）")

        # AI置信度说明
        impression_parts.append(f"\n注：本报告由AI辅助生成，置信度为{main_detection.confidence:.2%}，建议放射科医师审核确认。")

        return "\n".join(impression_parts)

    @staticmethod
    async def _generate_recommendation(detections: List[Detection]) -> str:
        """生成建议"""
        if not detections:
            return "建议定期体检复查。"

        recommendations = []

        # 根据置信度给出建议
        max_confidence = max(d.confidence for d in detections)

        if max_confidence > 0.9:
            recommendations.extend([
                "建议进一步行增强检查以明确诊断。",
                "建议结合临床资料和实验室检查结果综合分析。",
                "建议专科会诊。",
            ])
        elif max_confidence > 0.7:
            recommendations.extend([
                "建议短期随访复查。",
                "建议结合临床症状综合评估。",
            ])
        else:
            recommendations.append("建议定期复查。")

        return "\n".join(recommendations)

    @staticmethod
    async def get_report_by_study(
        db: AsyncSession,
        study_id: str
    ) -> Optional[Report]:
        """根据检查ID获取报告"""
        # 获取检查
        result = await db.execute(
            select(Study).where(Study.study_id == study_id)
        )
        study = result.scalar_one_or_none()

        if not study:
            return None

        # 获取报告
        result = await db.execute(
            select(Report)
            .options(selectinload(Report.radiologist))
            .options(selectinload(Report.reviewer))
            .where(Report.study_id == study.id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_report(
        db: AsyncSession,
        report_id: str,
        update_data: ReportUpdate,
        reviewer_id: Optional[str] = None
    ) -> Optional[Report]:
        """更新报告"""
        result = await db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()

        if not report:
            return None

        # 更新字段
        if update_data.findings is not None:
            report.findings = update_data.findings
        if update_data.impression is not None:
            report.impression = update_data.impression
        if update_data.recommendation is not None:
            report.recommendation = update_data.recommendation
        if update_data.clinical_history is not None:
            report.clinical_history = update_data.clinical_history
        if update_data.review_comment is not None:
            report.review_comment = update_data.review_comment

        # 如果有审核人，更新状态
        if reviewer_id:
            report.reviewer_id = reviewer_id
            report.status = ReportStatus.REVIEWED

        await db.commit()
        await db.refresh(report)

        logger.info(f"更新报告: {report_id}")
        return report

    @staticmethod
    async def sign_report(
        db: AsyncSession,
        report_id: str,
        radiologist_id: str
    ) -> Optional[Report]:
        """签发报告"""
        result = await db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()

        if not report:
            return None

        if report.radiologist_id != radiologist_id:
            raise ValueError("只能签发自己创建的报告")

        report.status = ReportStatus.SIGNED
        report.signed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(report)

        logger.info(f"签发报告: {report_id}")
        return report

    @staticmethod
    async def list_reports(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: Optional[ReportStatus] = None,
        radiologist_id: Optional[str] = None
    ) -> tuple[int, List[Report]]:
        """获取报告列表"""
        query = select(Report).options(selectinload(Report.radiologist))

        if status:
            query = query.where(Report.status == status)

        if radiologist_id:
            query = query.where(Report.radiologist_id == radiologist_id)

        # 获取总数
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # 分页
        query = query.order_by(desc(Report.created_at))
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        reports = result.scalars().all()

        return total, reports
