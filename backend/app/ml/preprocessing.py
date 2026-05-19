"""影像预处理工具"""
import numpy as np
from scipy.ndimage import median_filter, zoom
from typing import Dict, Tuple


def normalize_intensity(array: np.ndarray) -> np.ndarray:
    """强度归一化到 [0, 1]"""
    arr = array.astype(np.float32)
    min_val, max_val = arr.min(), arr.max()
    if max_val - min_val < 1e-8:
        return np.zeros_like(arr)
    return (arr - min_val) / (max_val - min_val)


def apply_window(array: np.ndarray, window: str = "lung") -> np.ndarray:
    """应用CT窗宽窗位"""
    windows = {
        "lung": {"center": -600, "width": 1500},
        "soft_tissue": {"center": 50, "width": 400},
        "bone": {"center": 300, "width": 1500},
        "brain": {"center": 40, "width": 80},
        "liver": {"center": 40, "width": 350},
        "abdomen": {"center": 40, "width": 400},
    }
    w = windows.get(window, windows["lung"])
    min_val = w["center"] - w["width"] // 2
    max_val = w["center"] + w["width"] // 2
    return np.clip(array, min_val, max_val)


def resample(array: np.ndarray, target_spacing: Tuple[float, ...] = (1.0, 1.0, 1.0),
             current_spacing: Tuple[float, ...] = None) -> np.ndarray:
    """重采样到目标分辨率"""
    if current_spacing is None:
        return array
    zoom_factors = [c / t for c, t in zip(current_spacing, target_spacing)]
    return zoom(array, zoom_factors, order=1)


def remove_noise(array: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """中值滤波去噪"""
    return median_filter(array, size=kernel_size)


def get_window_for_body_part(body_part: str) -> str:
    """根据检查部位选择窗宽窗位"""
    mapping = {
        "CHEST": "lung",
        "HEAD": "brain",
        "ABDOMEN": "liver",
        "PELVIS": "soft_tissue",
        "SPINE": "bone",
        "EXTREMITY": "bone",
    }
    return mapping.get(body_part, "lung")


def preprocess_pipeline(array: np.ndarray, body_part: str = "CHEST") -> np.ndarray:
    """完整预处理流水线"""
    result = normalize_intensity(array)
    window = get_window_for_body_part(body_part)
    result = apply_window(result, window)
    result = normalize_intensity(result)
    result = remove_noise(result)
    return result
