"""诊断Agent - 基于检测结果进行诊断推理"""
from typing import Any, Dict, List
from app.agents.base import BaseAgent
from app.core.logger import logger


class DiagnosisAgent(BaseAgent):
    """诊断推理Agent"""

    def __init__(self):
        super().__init__("DiagnosisAgent", "基于检测结果进行诊断推理")

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行诊断推理
        输入: { detections, findings, patient_info }
        输出: { primary_diagnosis, differential_diagnosis, risk_level, recommendations }
        """
        detections = input_data.get("detections", [])
        patient_info = input_data.get("patient_info")

        logger.info(f"DiagnosisAgent: 开始诊断推理，检测数={len(detections)}")

        # 尝试用LLM诊断
        if self.llm and detections:
            llm_result = await self._llm_diagnose(detections, patient_info)
            if llm_result:
                return llm_result

        # 降级到规则引擎
        return self._rule_based_diagnose(detections)

    async def _llm_diagnose(self, detections: List[Dict], patient_info: Dict) -> Dict[str, Any]:
        """使用LLM进行诊断推理"""
        det_summary = "\n".join([
            f"- {d['label']}，置信度{d['confidence']:.2%}"
            for d in detections
        ])

        patient_context = ""
        if patient_info:
            patient_context = f"患者信息：{patient_info.get('name', '')}，{patient_info.get('gender', '')}，{patient_info.get('age', '')}岁"

        prompt = f"""你是资深放射科医生。请基于以下AI检测结果给出诊断意见。

{patient_context}

检测结果：
{det_summary}

请用JSON格式返回：
{{
    "primary_diagnosis": "主要诊断",
    "differential_diagnosis": [
        {{"diagnosis": "诊断名称", "probability": 0.8}}
    ],
    "risk_level": "high/medium/low",
    "recommendations": ["建议1", "建议2"]
}}"""

        response = await self._llm_invoke(prompt)
        if response:
            result = self._extract_json(response)
            if result:
                logger.info("DiagnosisAgent: LLM诊断完成")
                return result
            logger.warning("DiagnosisAgent: LLM响应JSON解析失败，降级为规则引擎")
        return None

    def _rule_based_diagnose(self, detections: List[Dict]) -> Dict[str, Any]:
        """基于规则的诊断"""
        if not detections:
            return {
                "primary_diagnosis": "未见异常",
                "differential_diagnosis": [],
                "risk_level": "low",
                "recommendations": ["建议定期体检复查。"],
            }

        primary = detections[0]["label"]
        max_conf = max(d["confidence"] for d in detections)

        risk = "low"
        if max_conf > 0.9:
            risk = "high"
        elif max_conf > 0.7:
            risk = "medium"

        differential = []
        labels = set(d["label"] for d in detections)
        for label in labels:
            avg_conf = sum(d["confidence"] for d in detections if d["label"] == label) / \
                       max(1, sum(1 for d in detections if d["label"] == label))
            differential.append({"diagnosis": label, "probability": round(avg_conf, 2)})

        recs = []
        if risk == "high":
            recs = ["建议进一步行增强检查以明确诊断。", "建议结合临床资料和实验室检查结果综合分析。", "建议专科会诊。"]
        elif risk == "medium":
            recs = ["建议短期随访复查。", "建议结合临床症状综合评估。"]
        else:
            recs = ["建议定期复查。"]

        return {
            "primary_diagnosis": primary,
            "differential_diagnosis": differential,
            "risk_level": risk,
            "recommendations": recs,
        }
