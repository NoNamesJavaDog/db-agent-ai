"""
OpenAI Compatible Client
Supports OpenAI, DeepSeek, Qwen, Ollama, etc.
"""
import json
import logging
from typing import Dict, List, Any
from .base import BaseLLMClient
from db_agent.i18n import t

logger = logging.getLogger(__name__)


class OpenAICompatibleClient(BaseLLMClient):
    """OpenAI兼容的客户端 (支持 OpenAI, DeepSeek, Qwen, Ollama 等)"""

    def __init__(self, api_key: str, base_url: str, model: str, provider_name: str = "OpenAI"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.provider_name = provider_name

    def _handle_api_error(self, error) -> Dict[str, Any]:
        """Handle API errors and return appropriate error messages"""
        from openai import APIStatusError, APIConnectionError, APITimeoutError

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
                # Try to extract detail from error body
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
        from openai import APIStatusError, APIConnectionError, APITimeoutError

        # Only keep standard OpenAI message fields to avoid format errors
        # on OpenAI-compatible APIs (Qwen, DeepSeek, etc.).
        _MSG_FIELDS = {"role", "content", "name", "tool_calls", "tool_call_id"}
        _TC_FIELDS = {"id", "type", "function"}

        # Collect all tool_call_ids that have a matching tool response
        answered_tc_ids = set()
        for msg in messages:
            if msg.get("role") == "tool" and msg.get("tool_call_id"):
                answered_tc_ids.add(msg["tool_call_id"])

        cleaned_messages = []
        for msg in messages:
            m = {k: v for k, v in msg.items() if k in _MSG_FIELDS}
            if m.get("tool_calls"):
                # Filter out tool_calls that have no matching tool response
                valid_tcs = []
                for tc in m["tool_calls"]:
                    tc_clean = {k: v for k, v in tc.items() if k in _TC_FIELDS}
                    if tc.get("id") in answered_tc_ids:
                        valid_tcs.append(tc_clean)
                if valid_tcs:
                    m["tool_calls"] = valid_tcs
                else:
                    # All tool_calls are orphaned — send as plain text message
                    del m["tool_calls"]
                    if not m.get("content"):
                        m["content"] = " "
            # Merge consecutive messages with the same role (except tool)
            # to avoid API errors on providers that disallow them.
            if (cleaned_messages
                    and m.get("role") == cleaned_messages[-1].get("role")
                    and m["role"] in ("user", "assistant")
                    and not m.get("tool_calls")
                    and not cleaned_messages[-1].get("tool_calls")
                    and not m.get("tool_call_id")):
                prev = cleaned_messages[-1]
                prev["content"] = (prev.get("content") or "") + "\n" + (m.get("content") or "")
            else:
                cleaned_messages.append(m)

        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": cleaned_messages
        }
        if tools:
            kwargs["tools"] = tools

        # Debug: log message roles and structure
        for i, m in enumerate(cleaned_messages):
            tc_info = f", tool_calls={len(m['tool_calls'])}" if m.get('tool_calls') else ""
            tcid_info = f", tool_call_id={m.get('tool_call_id')}" if m.get('tool_call_id') else ""
            content_len = len(m.get('content') or '')
            logger.info(f"msg[{i}] role={m['role']}, content_len={content_len}{tc_info}{tcid_info}")

        try:
            response = self.client.chat.completions.create(**kwargs)
        except (APIStatusError, APIConnectionError, APITimeoutError) as e:
            return self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "finish_reason": "error",
                "content": t("llm_error_unknown", code="N/A", message=str(e)),
                "tool_calls": None
            }

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
            tool_calls_list = []
            for tc in message.tool_calls:
                try:
                    arguments = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse tool arguments: {tc.function.arguments}, error: {e}")
                    # Try to fix common JSON issues (e.g., single quotes, trailing commas)
                    try:
                        # Replace single quotes with double quotes
                        fixed_args = tc.function.arguments.replace("'", '"')
                        arguments = json.loads(fixed_args)
                    except json.JSONDecodeError:
                        arguments = {"raw_arguments": tc.function.arguments}

                tool_calls_list.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": arguments
                })
            result["tool_calls"] = tool_calls_list

        return result

    def get_provider_name(self) -> str:
        return self.provider_name

    def get_model_name(self) -> str:
        return self.model
