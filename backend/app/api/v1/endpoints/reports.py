"""报告相关API"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.schemas.user import User
from app.schemas.report import Report, ReportCreate, ReportUpdate
from app.models.study import Study
from app.services.report_service import ReportService
from app.core.logger import logger

router = APIRouter()


@router.post("/studies/{study_id}/reports", response_model=Report, status_code=status.HTTP_201_CREATED)
async def create_report(
    study_id: str,
    report_data: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建报告"""
    try:
        report = await ReportService.create_report(
            db,
            study_id,
            report_data,
            str(current_user.id),
            ai_generated=False
        )
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.post("/studies/{study_id}/reports/ai-generate", response_model=Report)
async def generate_ai_report(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """基于AI分析生成报告"""
    try:
        report = await ReportService.generate_ai_report(
            db,
            study_id,
            str(current_user.id)
        )
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"生成AI报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成失败: {str(e)}"
        )


@router.get("/studies/{study_id}/reports", response_model=Report)
async def get_study_report(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取检查的报告"""
    report = await ReportService.get_report_by_study(db, study_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )

    # 手动转换返回数据
    result_dict = {
        'id': str(report.id),
        'study_id': study_id,
        'radiologist_id': str(report.radiologist_id) if report.radiologist_id else None,
        'reviewer_id': str(report.reviewer_id) if report.reviewer_id else None,
        'report_type': report.report_type,
        'findings': report.findings,
        'impression': report.impression,
        'recommendation': report.recommendation,
        'clinical_history': report.clinical_history,
        'status': report.status.value if report.status else None,
        'ai_generated': report.ai_generated,
        'ai_confidence': report.ai_confidence,
        'review_comment': report.review_comment,
        'report_date': report.report_date.isoformat() if report.report_date else None,
        'signed_at': report.signed_at.isoformat() if report.signed_at else None,
        'created_at': report.created_at.isoformat() if report.created_at else None,
        'updated_at': report.updated_at.isoformat() if report.updated_at else None,
    }

    return result_dict


@router.put("/reports/{report_id}", response_model=Report)
async def update_report(
    report_id: str,
    update_data: ReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新报告"""
    try:
        report = await ReportService.update_report(
            db,
            report_id,
            update_data,
            str(current_user.id) if current_user.role in ["admin", "radiologist"] else None
        )

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告不存在"
            )

        # 手动转换返回数据
        result_dict = {
            'id': str(report.id),
            'study_id': str(report.study_id),
            'radiologist_id': str(report.radiologist_id) if report.radiologist_id else None,
            'reviewer_id': str(report.reviewer_id) if report.reviewer_id else None,
            'report_type': report.report_type,
            'findings': report.findings,
            'impression': report.impression,
            'recommendation': report.recommendation,
            'clinical_history': report.clinical_history,
            'status': report.status.value if report.status else None,
            'ai_generated': report.ai_generated,
            'ai_confidence': report.ai_confidence,
            'review_comment': report.review_comment,
            'report_date': report.report_date.isoformat() if report.report_date else None,
            'signed_at': report.signed_at.isoformat() if report.signed_at else None,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'updated_at': report.updated_at.isoformat() if report.updated_at else None,
        }

        return result_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.post("/reports/{report_id}/sign", response_model=Report)
async def sign_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """签发报告"""
    try:
        report = await ReportService.sign_report(
            db,
            report_id,
            str(current_user.id)
        )

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告不存在"
            )

        # 手动转换返回数据
        result_dict = {
            'id': str(report.id),
            'study_id': str(report.study_id),
            'radiologist_id': str(report.radiologist_id) if report.radiologist_id else None,
            'reviewer_id': str(report.reviewer_id) if report.reviewer_id else None,
            'report_type': report.report_type,
            'findings': report.findings,
            'impression': report.impression,
            'recommendation': report.recommendation,
            'clinical_history': report.clinical_history,
            'status': report.status.value if report.status else None,
            'ai_generated': report.ai_generated,
            'ai_confidence': report.ai_confidence,
            'review_comment': report.review_comment,
            'report_date': report.report_date.isoformat() if report.report_date else None,
            'signed_at': report.signed_at.isoformat() if report.signed_at else None,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'updated_at': report.updated_at.isoformat() if report.updated_at else None,
        }

        return result_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"签发报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"签发失败: {str(e)}"
        )


@router.get("/reports", response_model=dict)
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报告列表"""
    from app.models.report import ReportStatus

    status_enum = None
    if status:
        try:
            status_enum = ReportStatus(status)
        except ValueError:
            pass

    total, reports = await ReportService.list_reports(
        db,
        skip=skip,
        limit=limit,
        status=status_enum,
        radiologist_id=str(current_user.id) if current_user.role != "admin" else None
    )

    # 手动转换返回数据
    items = []
    for report in reports:
        # 获取关联的检查号
        study_result = await db.execute(
            select(Study).where(Study.id == report.study_id)
        )
        study = study_result.scalar_one_or_none()

        items.append({
            'id': str(report.id),
            'study_id': study.study_id if study else str(report.study_id),
            'radiologist_id': str(report.radiologist_id) if report.radiologist_id else None,
            'reviewer_id': str(report.reviewer_id) if report.reviewer_id else None,
            'report_type': report.report_type,
            'findings': report.findings[:100] + '...' if len(report.findings) > 100 else report.findings,
            'impression': report.impression[:100] + '...' if len(report.impression) > 100 else report.impression,
            'status': report.status.value if report.status else None,
            'ai_generated': report.ai_generated,
            'created_at': report.created_at.isoformat() if report.created_at else None,
        })

    return {'total': total, 'items': items}


@router.delete("/reports/{report_id}", status_code=status.HTTP_200_OK)
async def delete_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除报告"""
    from sqlalchemy import delete as sql_delete
    from app.models.report import Report as ReportModel

    result = await db.execute(
        select(ReportModel).where(ReportModel.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )

    study_id = report.study_id

    # 删除报告
    await db.execute(sql_delete(ReportModel).where(ReportModel.id == report_id))

    # 如果检查状态是reported，回退到completed
    study_result = await db.execute(
        select(Study).where(Study.id == study_id)
    )
    study = study_result.scalar_one_or_none()
    if study and study.status.value == "reported":
        from app.models.study import StudyStatus
        study.status = StudyStatus.COMPLETED

    await db.commit()
    return {"success": True, "message": "报告已删除"}
