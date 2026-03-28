"""文本清洗与提取工具集。"""

import re
from typing import List


class TextCleaner:
    """清洗与处理提取的文本。"""

    @staticmethod
    def clean_text(text: str) -> str:
        """清洗提取的文本。"""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove control characters
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """从文本中提取电子邮件地址。"""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        return re.findall(email_pattern, text)

    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """从文本中提取电话号码。"""
        # Basic phone number patterns
        phone_patterns = [
            r"\b\d{3}-\d{3}-\d{4}\b",  # 123-456-7890
            r"\b\(\d{3}\)\s*\d{3}-\d{4}\b",  # (123) 456-7890
            r"\b\d{3}\.\d{3}\.\d{4}\b",  # 123.456.7890
            r"\b\d{10}\b",  # 1234567890
        ]

        phone_numbers = []
        for pattern in phone_patterns:
            phone_numbers.extend(re.findall(pattern, text))

        return phone_numbers
