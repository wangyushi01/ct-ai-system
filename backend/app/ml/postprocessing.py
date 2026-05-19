"""检测结果后处理工具"""
import numpy as np
from scipy.ndimage import label as connected_label
from typing import List, Dict, Any


def find_connected_regions(binary_mask: np.ndarray, min_area: int = 10) -> List[Dict[str, Any]]:
    """连通域分析，找到所有独立区域"""
    labeled, num_features = connected_label(binary_mask)
    regions = []

    for i in range(1, num_features + 1):
        mask = labeled == i
        area = int(np.sum(mask))
        if area < min_area:
            continue

        coords = np.argwhere(mask)
        center = coords.mean(axis=0)
        diameter = 2 * np.sqrt(area / np.pi)

        regions.append({
            "center": center.tolist(),
            "area": area,
            "diameter": float(diameter),
            "mask": mask,
        })

    regions.sort(key=lambda r: r["area"], reverse=True)
    return regions


def compute_confidence(mean_intensity: float, area: int, base: float = 0.6) -> float:
    """基于区域特征计算置信度"""
    conf = base + mean_intensity * 0.2 + min(area / 1000, 0.15)
    return round(min(0.98, max(0.5, conf)), 3)


def nms_detections(detections: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
    """非极大值抑制，去除重叠检测"""
    if len(detections) <= 1:
        return detections

    sorted_dets = sorted(detections, key=lambda d: d.get("confidence", 0), reverse=True)
    kept = [sorted_dets[0]]

    for det in sorted_dets[1:]:
        loc = det.get("location", {})
        overlap = False
        for k in kept:
            kloc = k.get("location", {})
            if (abs(loc.get("x", 0) - kloc.get("x", 0)) < 20 and
                abs(loc.get("y", 0) - kloc.get("y", 0)) < 20 and
                abs(loc.get("z", 0) - kloc.get("z", 0)) < 5):
                overlap = True
                break
        if not overlap:
            kept.append(det)

    return kept
