"""
Anthropic Claude Client
"""
from typing import Dict, List, Any
from .base import BaseLLMClient


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude 客户端"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def chat(self, messages: List[Dict], tools: List[Dict] = None) -> Dict[str, Any]:
        # 提取 system 消息
        system_prompt = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                chat_messages.append(msg)

        # 转换工具格式为 Claude 格式
        claude_tools = None
        if tools:
            claude_tools = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool["function"]
                    claude_tools.append({
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {"type": "object", "properties": {}})
                    })

        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": chat_messages
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if claude_tools:
            kwargs["tools"] = claude_tools

        response = self.client.messages.create(**kwargs)

        result = {
            "finish_reason": "stop" if response.stop_reason == "end_turn" else response.stop_reason,
            "content": "",
            "tool_calls": None
        }

        tool_calls = []
        for block in response.content:
            if hasattr(block, "text"):
                result["content"] += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input
                })

        if tool_calls:
            result["finish_reason"] = "tool_calls"
            result["tool_calls"] = tool_calls

        return result

    def get_provider_name(self) -> str:
        return "Claude"

    def get_model_name(self) -> str:
        return self.model
