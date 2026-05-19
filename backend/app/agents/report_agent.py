"""报告生成Agent - 生成结构化诊断报告"""
from typing import Any, Dict
from app.agents.base import BaseAgent
from app.core.logger import logger


class ReportAgent(BaseAgent):
    """报告生成Agent"""

    def __init__(self):
        super().__init__("ReportAgent", "生成结构化诊断报告")

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成诊断报告
        输入: { detections, diagnosis, study_info }
        输出: { findings, impression, recommendation }
        """
        detections = input_data.get("detections", [])
        diagnosis = input_data.get("diagnosis", {})
        study_info = input_data.get("study_info", {})

        logger.info("ReportAgent: 开始生成报告")

        # 尝试用LLM生成
        if self.llm and (detections or diagnosis):
            llm_result = await self._llm_generate(detections, diagnosis, study_info)
            if llm_result:
                return llm_result

        # 降级到模板生成
        return self._template_generate(detections, diagnosis, study_info)

    async def _llm_generate(self, detections, diagnosis, study_info) -> Dict[str, Any]:
        """使用LLM生成报告"""
        det_text = "\n".join([f"- {d['label']}，置信度{d['confidence']:.2%}" for d in detections])
        diag_text = f"主诊断：{diagnosis.get('primary_diagnosis', '无')}，风险：{diagnosis.get('risk_level', 'unknown')}"

        prompt = f"""你是医学报告撰写专家。请基于以下信息生成CT诊断报告。

检测结果：
{det_text}

诊断结论：
{diag_text}

请用JSON格式返回：
{{
    "findings": "详细的影像发现描述",
    "impression": "诊断意见",
    "recommendation": "后续建议"
}}"""

        response = await self._llm_invoke(prompt)
        if response:
            result = self._extract_json(response)
            if result:
                logger.info("ReportAgent: LLM报告生成完成")
                return result
            logger.warning("ReportAgent: LLM响应JSON解析失败，降级为模板生成")
        return None

    def _template_generate(self, detections, diagnosis, study_info) -> Dict[str, Any]:
        """基于模板生成报告"""
        modality = study_info.get("modality", "CT")
        body_part = study_info.get("body_part", "")

        # 影像发现
        findings_parts = [f"检查类型：{modality}，检查部位：{body_part}。"]
        if not detections:
            findings_parts.append("\n影像表现：未见明显异常。")
        else:
            findings_parts.append(f"\n影像表现：发现{len(detections)}个异常病灶。")
            for i, det in enumerate(detections, 1):
                info = f"\n{i}. {det['label']}（置信度：{det['confidence']:.2%}）"
                if det.get("location"):
                    loc = det["location"]
                    loc_parts = []
                    if "x" in loc: loc_parts.append(f"X:{loc['x']:.1f}mm")
                    if "y" in loc: loc_parts.append(f"Y:{loc['y']:.1f}mm")
                    if "region" in loc: loc_parts.append(loc["region"])
                    if "side" in loc: loc_parts.append(loc["side"])
                    if loc_parts:
                        info += f"\n   位置：{' '.join(loc_parts)}"
                if det.get("size"):
                    if det["size"].get("diameter"):
                        info += f"\n   大小：直径{det['size']['diameter']:.1f}mm"
                if det.get("properties"):
                    props = [f"{k}：{v}" for k, v in det["properties"].items()]
                    info += f"\n   特征：{', '.join(props)}"
                findings_parts.append(info)

        # 诊断意见
        if not detections:
            impression = "影像学表现未见明显异常。"
        else:
            sorted_dets = sorted(detections, key=lambda d: d["confidence"], reverse=True)
            impression_parts = []
            for i, det in enumerate(sorted_dets[:3], 1):
                impression_parts.append(f"{i}. {det['label']}（置信度：{det['confidence']:.2%}）")
            impression_parts.append(f"\n注：本报告由AI辅助生成，建议放射科医师审核确认。")
            impression = "\n".join(impression_parts)

        # 建议
        risk = diagnosis.get("risk_level", "low")
        if risk == "high":
            recommendation = "建议进一步行增强检查以明确诊断。\n建议结合临床资料和实验室检查结果综合分析。\n建议专科会诊。"
        elif risk == "medium":
            recommendation = "建议短期随访复查。\n建议结合临床症状综合评估。"
        else:
            recommendation = "建议定期复查。"

        return {
            "findings": "\n".join(findings_parts),
            "impression": impression,
            "recommendation": recommendation,
        }
