"""API路由聚合"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, studies, analysis, reports, upload

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 检查相关路由
api_router.include_router(studies.router, prefix="/studies", tags=["检查"])

# 分析相关路由
api_router.include_router(analysis.router, prefix="/analysis", tags=["分析"])

# 报告相关路由
api_router.include_router(reports.router, prefix="", tags=["报告"])

# 上传相关路由
api_router.include_router(upload.router, prefix="/upload", tags=["上传"])
