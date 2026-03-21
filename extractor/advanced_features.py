"""向后兼容垫片。请直接使用 anti_detection 和 form_handler 模块。"""

from .anti_detection import AntiDetectionScraper
from .form_handler import FormHandler

__all__ = ["AntiDetectionScraper", "FormHandler"]
