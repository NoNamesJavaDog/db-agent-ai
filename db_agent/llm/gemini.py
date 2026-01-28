"""
Google Gemini Client
"""
import logging
from typing import Dict, List, Any
from .base import BaseLLMClient
from db_agent.i18n import t

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Google Gemini 客户端"""

    def __init__(self, api_key: str, model: str = "gemini-pro"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)

    def chat(self, messages: List[Dict], tools: List[Dict] = None) -> Dict[str, Any]:
        # 转换消息格式
        gemini_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # Gemini 没有 system role，放到第一条 user 消息
                continue
            role = "user" if msg["role"] == "user" else "model"
            gemini_messages.append({
                "role": role,
                "parts": [msg["content"]] if isinstance(msg["content"], str) else msg["content"]
            })

        try:
            # Gemini 工具调用支持较复杂，这里简化处理
            response = self.model.generate_content(gemini_messages)

            return {
                "finish_reason": "stop",
                "content": response.text if response.text else "",
                "tool_calls": None
            }
        except Exception as e:
            error_str = str(e)
            logger.error(f"Gemini API error: {error_str}")

            # Parse common Gemini errors
            if "API key" in error_str or "401" in error_str:
                error_message = t("llm_error_401")
            elif "quota" in error_str.lower() or "429" in error_str:
                error_message = t("llm_error_429")
            elif "500" in error_str:
                error_message = t("llm_error_500")
            elif "503" in error_str:
                error_message = t("llm_error_503")
            else:
                error_message = t("llm_error_unknown", code="N/A", message=error_str)

            return {
                "finish_reason": "error",
                "content": error_message,
                "tool_calls": None
            }

    def get_provider_name(self) -> str:
        return "Gemini"

    def get_model_name(self) -> str:
        return self.model_name
