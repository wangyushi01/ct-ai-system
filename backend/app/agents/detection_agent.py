"""检测Agent - 负责CT影像中病灶的检测和定位"""
from typing import Any, Dict, List
from app.agents.base import BaseAgent
from app.ml.models.lung_nodule import LungNoduleDetector
from app.ml.models.pneumonia import PneumoniaDetector
from app.ml.models.brain_hemorrhage import BrainHemorrhageDetector
from app.ml.models.liver_lesion import LiverLesionDetector
from app.core.logger import logger


class DetectionAgent(BaseAgent):
    """病灶检测Agent"""

    def __init__(self):
        super().__init__("DetectionAgent", "负责CT影像中病灶的检测和定位")
        self.detectors = {
            "lung_nodule": LungNoduleDetector(),
            "pneumonia": PneumoniaDetector(),
            "brain_hemorrhage": BrainHemorrhageDetector(),
            "liver_lesion": LiverLesionDetector(),
        }

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行检测任务
        输入: { images, analysis_type }
        输出: { detections: [...], findings }
        """
        images = input_data.get("images", [])
        analysis_type = input_data.get("analysis_type", "lung_nodule")

        logger.info(f"DetectionAgent: 开始检测，类型={analysis_type}，影像数={len(images)}")

        # 选择对应的检测器
        detector = self.detectors.get(analysis_type)
        if not detector:
            # 尝试所有检测器
            all_detections = []
            for name, det in self.detectors.items():
                dets = det.detect(images)
                all_detections.extend(dets)
            detections = all_detections
        else:
            detections = detector.detect(images)

        # 生成影像发现描述
        findings = self._generate_findings(detections, analysis_type)

        result = {
            "detections": detections,
            "findings": findings,
            "analysis_type": analysis_type,
            "image_count": len(images),
        }

        logger.info(f"DetectionAgent: 检测完成，发现 {len(detections)} 个病灶")
        return result

    def _generate_findings(self, detections: List[Dict], analysis_type: str) -> str:
        """生成影像发现描述"""
        if not detections:
            return "影像未见明显异常。"

        parts = [f"发现{len(detections)}个异常病灶。"]
        for i, det in enumerate(detections, 1):
            info = f"{i}. {det['label']}（置信度：{det['confidence']:.2%}）"
            if det.get("size", {}).get("diameter"):
                info += f"，直径{det['size']['diameter']:.1f}mm"
            parts.append(info)

        return "\n".join(parts)
