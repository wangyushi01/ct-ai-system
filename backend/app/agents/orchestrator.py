"""Agent编排器 - 协调多Agent执行分析流水线"""
from typing import Any, Dict, Optional
from app.agents.preprocess_agent import PreprocessAgent
from app.agents.detection_agent import DetectionAgent
from app.agents.diagnosis_agent import DiagnosisAgent
from app.agents.report_agent import ReportAgent
from app.core.logger import logger


class AgentOrchestrator:
    """Agent编排器"""

    def __init__(self):
        self.preprocess_agent = PreprocessAgent()
        self.detection_agent = DetectionAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.report_agent = ReportAgent()
        logger.info("AgentOrchestrator: 编排器初始化完成（4个Agent就绪）")

    async def analyze(
        self,
        study_id: str,
        analysis_type: str,
        patient_info: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        执行完整分析流水线: 预处理 → 检测 → 诊断 → 报告生成
        """
        logger.info(f"Orchestrator: 开始分析流水线 study={study_id} type={analysis_type}")

        # 第1步: 预处理
        body_part = self._get_body_part(analysis_type)
        preprocess_result = await self.preprocess_agent.run({
            "study_id": study_id,
            "body_part": body_part,
        })

        # 第2步: 检测
        detection_result = await self.detection_agent.run({
            "images": preprocess_result["images"],
            "analysis_type": analysis_type,
        })

        # 第3步: 诊断
        diagnosis_result = await self.diagnosis_agent.run({
            "detections": detection_result["detections"],
            "findings": detection_result["findings"],
            "patient_info": patient_info,
        })

        # 第4步: 报告生成
        report_result = await self.report_agent.run({
            "detections": detection_result["detections"],
            "diagnosis": diagnosis_result,
            "study_info": {
                "study_id": study_id,
                "analysis_type": analysis_type,
                "modality": "CT",
                "body_part": body_part,
            },
        })

        # 汇总结果
        result = {
            "detections": detection_result["detections"],
            "findings": detection_result["findings"],
            "diagnosis": diagnosis_result,
            "report": report_result,
        }

        logger.info(f"Orchestrator: 分析流水线完成，检测={len(detection_result['detections'])}个病灶")
        return result

    async def analyze_study(
        self,
        study_id: str,
        analysis_type: str,
        patient_info: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """兼容旧接口的分析入口"""
        return await self.analyze(study_id, analysis_type, patient_info)

    def _get_body_part(self, analysis_type: str) -> str:
        """根据分析类型推断检查部位"""
        mapping = {
            "lung_nodule": "CHEST",
            "pneumonia": "CHEST",
            "brain_hemorrhage": "HEAD",
            "liver_lesion": "ABDOMEN",
        }
        return mapping.get(analysis_type, "CHEST")
