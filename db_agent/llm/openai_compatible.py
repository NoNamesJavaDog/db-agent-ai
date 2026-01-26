"""
OpenAI Compatible Client
Supports OpenAI, DeepSeek, Qwen, Ollama, etc.
"""
import json
from typing import Dict, List, Any
from .base import BaseLLMClient


class OpenAICompatibleClient(BaseLLMClient):
    """OpenAI兼容的客户端 (支持 OpenAI, DeepSeek, Qwen, Ollama 等)"""

    def __init__(self, api_key: str, base_url: str, model: str, provider_name: str = "OpenAI"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.provider_name = provider_name

    def chat(self, messages: List[Dict], tools: List[Dict] = None) -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages
        }
        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)

        if not response.choices:
            return {
                "finish_reason": "error",
                "content": "No response from API",
                "tool_calls": None
            }

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        result = {
            "finish_reason": finish_reason,
            "content": message.content,
            "tool_calls": None
        }

        # Handle tool_calls - finish_reason might be "tool_calls" or "stop" with tool_calls present
        if message.tool_calls:
            result["finish_reason"] = "tool_calls"
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments) if tc.function.arguments else {}
                }
                for tc in message.tool_calls
            ]

        return result

    def get_provider_name(self) -> str:
        return self.provider_name

    def get_model_name(self) -> str:
        return self.model
