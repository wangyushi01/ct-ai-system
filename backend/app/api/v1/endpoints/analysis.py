"""分析相关API"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import json
from datetime import datetime
from app.api.deps import get_db, get_current_user
from app.schemas.user import User
from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisTaskResponse,
    AnalysisResponse,
    DetectionItem
)
from app.models.study import Study
from app.models.analysis import AnalysisTask, Detection, TaskStatus, AnalysisType
from app.services.agent_service import ai_agent
from app.core.logger import logger

router = APIRouter()

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)

    def disconnect(self, task_id: str, websocket: WebSocket):
        if task_id in self.active_connections:
            self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

    async def send_update(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)

            # 清理断开的连接
            for conn in disconnected:
                self.active_connections[task_id].remove(conn)

manager = ConnectionManager()


@router.post("/analyze", status_code=status.HTTP_201_CREATED)
async def create_analysis(
    analysis_data: AnalysisCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建分析任务

    对指定的检查进行AI分析
    """
    # 验证检查是否存在
    result = await db.execute(
        select(Study).where(Study.study_id == analysis_data.study_id)
    )
    study = result.scalar_one_or_none()

    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检查不存在"
        )

    # 检查是否有影像
    if study.images_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传影像后再进行分析"
        )

    # 创建分析任务
    task = AnalysisTask(
        study_id=study.id,
        task_type=analysis_data.task_type,
        priority=analysis_data.priority,
        status=TaskStatus.RUNNING,
        started_at=datetime.utcnow()
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    logger.info(f"创建分析任务: {task.id}, 类型: {task.task_type}")

    # 异步执行分析
    import asyncio
    asyncio.create_task(run_analysis(task.id, analysis_data.study_id, task.task_type.value, str(current_user.id)))

    # 手动转换返回数据
    result_dict = {
        'id': str(task.id),
        'study_id': str(task.study_id),
        'task_type': task.task_type.value,
        'status': task.status.value,
        'priority': task.priority,
        'progress': task.progress,
        'error_message': task.error_message,
        'started_at': task.started_at.isoformat() if task.started_at else None,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'created_at': task.created_at.isoformat() if task.created_at else None,
        'detections': []
    }

    return result_dict


async def _save_llm_report(db, study_id: str, user_id: str, report_data: dict, diagnosis: dict, detections: list):
    """将Orchestrator的LLM报告直接保存到数据库"""
    from app.models.study import Study
    from app.models.report import Report
    import uuid as _uuid

    study_result = await db.execute(
        select(Study).where(Study.study_id == study_id)
    )
    study = study_result.scalar_one_or_none()
    if not study:
        raise ValueError("检查不存在")

    # 如果已有报告则更新，否则新建
    from sqlalchemy import select as _sel
    existing = await db.execute(
        _sel(Report).where(Report.study_id == study.id)
    )
    report = existing.scalar_one_or_none()

    if report:
        report.findings = report_data.get("findings", report.findings)
        report.impression = report_data.get("impression", report.impression)
        report.recommendation = report_data.get("recommendation", report.recommendation)
    else:
        max_conf = max((d.confidence for d in detections), default=0)
        report = Report(
            id=_uuid.uuid4(),
            study_id=study.id,
            radiologist_id=_uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
            report_type="CT诊断报告",
            findings=report_data.get("findings", ""),
            impression=report_data.get("impression", ""),
            recommendation=report_data.get("recommendation", ""),
            status="DRAFT",
            ai_generated=True,
            ai_confidence=max_conf,
            clinical_history=f"AI分析报告（DeepSeek辅助诊断）",
            report_date=datetime.utcnow(),
        )
        db.add(report)

    await db.commit()
    logger.info(f"LLM报告已保存: study={study_id}")


async def run_analysis(task_id: str, study_id: str, analysis_type: str, user_id: str):
    """执行分析任务（使用独立数据库会话）"""
    from app.db.session import AsyncSessionLocal
    from app.models.study import StudyStatus

    async with AsyncSessionLocal() as db:
        try:
            # 更新进度
            await manager.send_update(task_id, {
                "type": "progress",
                "progress": 10,
                "message": "开始分析..."
            })

            # 更新检查状态为分析中
            study_result = await db.execute(
                select(Study).where(Study.study_id == study_id)
            )
            study = study_result.scalar_one_or_none()
            if study:
                study.status = StudyStatus.ANALYZING
                await db.commit()

            await manager.send_update(task_id, {
                "type": "progress",
                "progress": 30,
                "message": "正在读取影像数据..."
            })

            # 执行AI分析
            result = await ai_agent.analyze_study(study_id, analysis_type)

            await manager.send_update(task_id, {
                "type": "progress",
                "progress": 60,
                "message": "AI分析完成，正在保存结果..."
            })

            # 保存检测结果
            detections = []
            for det_data in result.get("detections", []):
                detection = Detection(
                    task_id=task_id,
                    detection_type=analysis_type,
                    label=det_data["label"],
                    confidence=det_data["confidence"],
                    location=det_data.get("location", {}),
                    size=det_data.get("size"),
                    properties=det_data.get("properties")
                )
                db.add(detection)
                detections.append(detection)

            # 获取任务并更新状态
            task_result = await db.execute(
                select(AnalysisTask).where(AnalysisTask.id == task_id)
            )
            task = task_result.scalar_one_or_none()

            if task:
                task.status = TaskStatus.COMPLETED
                task.progress = 100
                task.completed_at = datetime.utcnow()

            # 更新检查状态为已完成
            if study:
                study.status = StudyStatus.COMPLETED

            await db.commit()

            # 自动生成AI报告（优先使用Orchestrator的LLM报告）
            try:
                report_data = result.get("report", {})
                diagnosis = result.get("diagnosis", {})
                if report_data:
                    await _save_llm_report(db, study_id, user_id, report_data, diagnosis, detections)
                else:
                    from app.services.report_service import ReportService
                    await ReportService.generate_ai_report(db, study_id, user_id)
                logger.info(f"自动生成AI报告: {study_id}")
            except ValueError:
                pass
            except Exception as report_err:
                logger.error(f"自动生成报告失败: {report_err}")

            # 发送完成通知
            await manager.send_update(task_id, {
                "type": "completed",
                "progress": 100,
                "message": "分析完成",
                "detections_count": len(detections)
            })

            logger.info(f"分析任务完成: {task_id}")

        except Exception as e:
            logger.error(f"分析任务失败: {e}")

            try:
                # 更新任务状态为失败
                task_result = await db.execute(
                    select(AnalysisTask).where(AnalysisTask.id == task_id)
                )
                task = task_result.scalar_one_or_none()

                if task:
                    task.status = TaskStatus.FAILED
                    task.error_message = str(e)

                # 更新检查状态回processing
                study_result = await db.execute(
                    select(Study).where(Study.study_id == study_id)
                )
                study = study_result.scalar_one_or_none()
                if study:
                    study.status = StudyStatus.PROCESSING

                await db.commit()
            except Exception as inner_e:
                logger.error(f"更新失败状态出错: {inner_e}")

            # 发送失败通知
            await manager.send_update(task_id, {
                "type": "error",
                "message": f"分析失败: {str(e)}"
            })


@router.get("/{task_id}", response_model=AnalysisTaskResponse)
async def get_analysis_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取分析任务状态和结果"""
    result = await db.execute(
        select(AnalysisTask).where(AnalysisTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 获取检测结果
    detections_result = await db.execute(
        select(Detection).where(Detection.task_id == task_id)
    )
    detections = detections_result.scalars().all()

    # 转换为响应格式
    task_response = AnalysisTaskResponse(
        id=str(task.id),
        study_id=str(task.study_id),
        task_type=task.task_type,
        status=task.status,
        priority=task.priority,
        progress=task.progress,
        error_message=task.error_message,
        started_at=task.started_at,
        completed_at=task.completed_at,
        created_at=task.created_at,
        detections=[
            DetectionItem(
                id=str(d.id),
                label=d.label,
                confidence=d.confidence,
                location=d.location,
                size=d.size,
                properties=d.properties
            )
            for d in detections
        ]
    )

    return task_response


@router.websocket("/ws/{task_id}")
async def analysis_websocket(
    task_id: str,
    websocket: WebSocket
):
    """
    分析任务进度推送

    实时推送分析进度
    """
    await manager.connect(task_id, websocket)

    try:
        while True:
            # 保持连接
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(task_id, websocket)


@router.get("", response_model=list[AnalysisTaskResponse])
async def list_analysis_tasks(
    skip: int = 0,
    limit: int = 20,
    status: TaskStatus = None,
    study_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取分析任务列表"""
    query = select(AnalysisTask)

    if status:
        query = query.where(AnalysisTask.status == status)

    if study_id:
        # study_id可能是字符串检查号或UUID
        study_result = await db.execute(
            select(Study).where(Study.study_id == study_id)
        )
        study_obj = study_result.scalar_one_or_none()
        if not study_obj:
            # 尝试按UUID查找
            import uuid as _uuid
            try:
                _uuid.UUID(study_id)
                study_result = await db.execute(
                    select(Study).where(Study.id == study_id)
                )
                study_obj = study_result.scalar_one_or_none()
            except ValueError:
                pass
        if study_obj:
            query = query.where(AnalysisTask.study_id == study_obj.id)
        else:
            return []

    query = query.order_by(AnalysisTask.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    # 获取每个任务的检测结果
    response_list = []
    for task in tasks:
        detections_result = await db.execute(
            select(Detection).where(Detection.task_id == task.id)
        )
        detections = detections_result.scalars().all()

        response_list.append(AnalysisTaskResponse(
            id=str(task.id),
            study_id=str(task.study_id),
            task_type=task.task_type,
            status=task.status,
            priority=task.priority,
            progress=task.progress,
            error_message=task.error_message,
            started_at=task.started_at,
            completed_at=task.completed_at,
            created_at=task.created_at,
            detections=[
                DetectionItem(
                    id=str(d.id),
                    label=d.label,
                    confidence=d.confidence,
                    location=d.location,
                    size=d.size,
                    properties=d.properties
                )
                for d in detections
            ]
        ))

    return response_list


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_analysis_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除分析任务"""
    from sqlalchemy import delete as sql_delete

    result = await db.execute(
        select(AnalysisTask).where(AnalysisTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    study_id = task.study_id

    # 删除检测结果
    await db.execute(sql_delete(Detection).where(Detection.task_id == task_id))
    # 删除任务
    await db.execute(sql_delete(AnalysisTask).where(AnalysisTask.id == task_id))

    # 检查该检查是否还有其他分析任务
    remaining = await db.execute(
        select(AnalysisTask).where(AnalysisTask.study_id == study_id).limit(1)
    )
    if not remaining.scalar_one_or_none():
        # 没有其他任务了，状态回退
        from app.models.study import Study as StudyModel, StudyStatus as SS
        study_result = await db.execute(
            select(StudyModel).where(StudyModel.id == study_id)
        )
        study = study_result.scalar_one_or_none()
        if study and study.status == SS.COMPLETED:
            study.status = SS.PROCESSING

    await db.commit()
    return {"success": True, "message": "分析任务已删除"}
