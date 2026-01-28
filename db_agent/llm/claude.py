"""
Anthropic Claude Client
"""
import logging
from typing import Dict, List, Any
from .base import BaseLLMClient
from db_agent.i18n import t

logger = logging.getLogger(__name__)


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude 客户端"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", base_url: str = None):
        from anthropic import Anthropic
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = Anthropic(**kwargs)
        self.model = model

    def _handle_api_error(self, error) -> Dict[str, Any]:
        """Handle API errors and return appropriate error messages"""
        from anthropic import APIStatusError, APIConnectionError, APITimeoutError

        error_message = str(error)

        if isinstance(error, APIConnectionError):
            error_message = t("llm_error_connection", error=str(error))
        elif isinstance(error, APITimeoutError):
            error_message = t("llm_error_timeout")
        elif isinstance(error, APIStatusError):
            status_code = error.status_code
            if status_code == 400:
                error_message = t("llm_error_400")
            elif status_code == 401:
                error_message = t("llm_error_401")
            elif status_code == 402:
                error_message = t("llm_error_402")
            elif status_code == 422:
                detail = ""
                try:
                    if hasattr(error, 'body') and error.body:
                        detail = str(error.body.get('error', {}).get('message', ''))
                except Exception:
                    pass
                error_message = t("llm_error_422", detail=detail or str(error))
            elif status_code == 429:
                error_message = t("llm_error_429")
            elif status_code == 500:
                error_message = t("llm_error_500")
            elif status_code == 503:
                error_message = t("llm_error_503")
            else:
                error_message = t("llm_error_unknown", code=status_code, message=str(error))

        logger.error(f"API error: {error_message}")

        return {
            "finish_reason": "error",
            "content": error_message,
            "tool_calls": None
        }

    def chat(self, messages: List[Dict], tools: List[Dict] = None) -> Dict[str, Any]:
        from anthropic import APIStatusError, APIConnectionError, APITimeoutError

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

        try:
            response = self.client.messages.create(**kwargs)
        except (APIStatusError, APIConnectionError, APITimeoutError) as e:
            return self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "finish_reason": "error",
                "content": t("llm_error_unknown", code="N/A", message=str(e)),
                "tool_calls": None
            }

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
