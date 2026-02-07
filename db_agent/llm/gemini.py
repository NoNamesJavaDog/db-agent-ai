"""
Google Gemini Client (google-genai SDK)
"""
import base64
import json
import logging
from typing import Dict, List, Any
from .base import BaseLLMClient
from db_agent.i18n import t

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Google Gemini 客户端 — 基于新版 google-genai SDK"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", base_url: str = None):
        from google import genai
        from google.genai import types

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["http_options"] = types.HttpOptions(base_url=base_url)

        self.client = genai.Client(**client_kwargs)
        self.model_name = model

    def _convert_tools(self, tools: List[Dict]) -> List[Any]:
        """Convert OpenAI tool format to Gemini Tool objects."""
        from google.genai import types

        declarations = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                params = func.get("parameters")

                declarations.append(
                    types.FunctionDeclaration(
                        name=func["name"],
                        description=func.get("description", ""),
                        parameters_json_schema=params if params else None,
                    )
                )

        if not declarations:
            return []

        return [types.Tool(function_declarations=declarations)]

    def _convert_messages(self, messages: List[Dict]) -> tuple:
        """Convert OpenAI message format to Gemini format.

        Returns:
            (system_instruction, gemini_contents)
        """
        from google.genai import types

        system_instruction = None
        gemini_contents = []

        # Build tool_call_id → tool_name mapping from assistant messages
        id_to_name = {}
        for msg in messages:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    tc_id = tc.get("id", "")
                    func = tc.get("function", {})
                    tc_name = func.get("name", "") if isinstance(func, dict) else ""
                    if tc_id and tc_name:
                        id_to_name[tc_id] = tc_name

        # Sanitize messages: ensure tool messages always follow an assistant
        # message with tool_calls.  Orphan tool messages (e.g. after context
        # compression) would cause Gemini API to reject the request.
        sanitized: list[dict] = []
        last_assistant_has_tc = False
        for msg in messages:
            role = msg.get("role", "")
            if role == "tool":
                if not last_assistant_has_tc:
                    # Orphan tool response — convert to user context message
                    sanitized.append({
                        "role": "user",
                        "content": f"[Previous tool result]: {msg.get('content', '')}"
                    })
                    continue
            if role == "assistant":
                last_assistant_has_tc = bool(msg.get("tool_calls"))
            else:
                if role != "tool":
                    last_assistant_has_tc = False
            sanitized.append(msg)
        messages = sanitized

        # Pending function response parts to be merged
        pending_fn_responses = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "") or ""

            if role == "system":
                system_instruction = content
                continue

            elif role == "user":
                # Flush any pending function responses before user message
                if pending_fn_responses:
                    gemini_contents.append(
                        types.Content(role="user", parts=list(pending_fn_responses))
                    )
                    pending_fn_responses = []

                gemini_contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=content if content else " ")]
                    )
                )

            elif role == "assistant":
                # Flush any pending function responses before model message
                if pending_fn_responses:
                    gemini_contents.append(
                        types.Content(role="user", parts=list(pending_fn_responses))
                    )
                    pending_fn_responses = []

                parts = []
                if content:
                    parts.append(types.Part.from_text(text=content))

                # Convert tool_calls to FunctionCall parts
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        func = tc.get("function", {})
                        name = func.get("name", "") if isinstance(func, dict) else ""
                        args_str = func.get("arguments", "{}") if isinstance(func, dict) else "{}"
                        try:
                            args = json.loads(args_str) if isinstance(args_str, str) else args_str
                        except json.JSONDecodeError:
                            args = {}

                        part_kwargs = {
                            "function_call": types.FunctionCall(
                                name=name, args=args
                            )
                        }
                        # Restore thought_signature if present — required by
                        # Gemini API for multi-turn function calling.
                        # Decode base64 string → bytes.
                        thought_sig = tc.get("thought_signature")
                        if thought_sig:
                            if isinstance(thought_sig, str):
                                thought_sig = base64.b64decode(thought_sig)
                            part_kwargs["thought_signature"] = thought_sig

                        parts.append(types.Part(**part_kwargs))

                if not parts:
                    parts.append(types.Part.from_text(text=" "))

                gemini_contents.append(
                    types.Content(role="model", parts=parts)
                )

            elif role == "tool":
                # Accumulate tool responses — flushed as one "tool" role message
                tool_call_id = msg.get("tool_call_id", "")
                fn_name = id_to_name.get(tool_call_id, "unknown")

                # Parse tool result content
                try:
                    result_data = json.loads(content) if isinstance(content, str) else content
                except json.JSONDecodeError:
                    result_data = {"result": content}

                if not isinstance(result_data, dict):
                    result_data = {"result": result_data}

                pending_fn_responses.append(
                    types.Part.from_function_response(
                        name=fn_name, response=result_data
                    )
                )

        # Flush any remaining function responses
        if pending_fn_responses:
            gemini_contents.append(
                types.Content(role="user", parts=list(pending_fn_responses))
            )

        return system_instruction, gemini_contents

    def chat(self, messages: List[Dict], tools: List[Dict] = None) -> Dict[str, Any]:
        from google.genai import types

        # Convert messages and extract system instruction
        system_instruction, gemini_contents = self._convert_messages(messages)

        # Build GenerateContentConfig
        config_kwargs = {
            # Disable SDK's automatic function calling — we handle tool
            # execution ourselves in the agent loop.
            "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        # Enable thinking for thinking models (e.g. gemini-2.5-flash, gemini-3-flash-preview)
        model_lower = self.model_name.lower()
        if "thinking" in model_lower or "2.5" in model_lower or "3-" in model_lower:
            config_kwargs["thinking_config"] = types.ThinkingConfig(include_thoughts=True, thinking_budget=2048)

        if tools:
            gemini_tools = self._convert_tools(tools)
            if gemini_tools:
                config_kwargs["tools"] = gemini_tools

        config = types.GenerateContentConfig(**config_kwargs)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=gemini_contents,
                config=config,
            )

            # Parse response parts
            content_parts = []
            thought_parts = []
            tool_calls = []

            all_parts = list(response.candidates[0].content.parts) if (
                response.candidates and response.candidates[0].content
                and response.candidates[0].content.parts
            ) else []

            for part in all_parts:
                if part.text:
                    if getattr(part, 'thought', False):
                        thought_parts.append(part.text)
                    else:
                        content_parts.append(part.text)
                if part.function_call:
                    fc = part.function_call
                    args = dict(fc.args) if fc.args else {}
                    tc = {
                        "id": f"call_{fc.name}_{len(tool_calls)}",
                        "name": fc.name,
                        "arguments": args,
                    }
                    # Preserve thought_signature — required by Gemini API
                    # for multi-turn function calling conversations.
                    # Encode bytes → base64 string for JSON serialization.
                    if getattr(part, 'thought_signature', None):
                        sig = part.thought_signature
                        tc["thought_signature"] = base64.b64encode(sig).decode("ascii") if isinstance(sig, bytes) else sig
                    tool_calls.append(tc)

            # Merge thought text into content so the user sees the reasoning
            all_text = "".join(thought_parts) + "".join(content_parts)

            result = {
                "finish_reason": "stop",
                "content": all_text,
                "tool_calls": None,
            }

            if tool_calls:
                result["finish_reason"] = "tool_calls"
                result["tool_calls"] = tool_calls

            return result

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
