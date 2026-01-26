"""
Google Gemini Client
"""
from typing import Dict, List, Any
from .base import BaseLLMClient


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

        # Gemini 工具调用支持较复杂，这里简化处理
        response = self.model.generate_content(gemini_messages)

        return {
            "finish_reason": "stop",
            "content": response.text if response.text else "",
            "tool_calls": None
        }

    def get_provider_name(self) -> str:
        return "Gemini"

    def get_model_name(self) -> str:
        return self.model_name
