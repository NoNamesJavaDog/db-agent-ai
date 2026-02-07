"""Context compression for managing conversation history"""
import json
import logging
from typing import List, Dict, Any, Tuple, TYPE_CHECKING

from .token_counter import TokenCounter

if TYPE_CHECKING:
    from db_agent.llm import BaseLLMClient

logger = logging.getLogger(__name__)

# 默认保留最近的消息数量
DEFAULT_KEEP_RECENT = 10

# 默认触发压缩的上下文使用百分比
COMPRESSION_THRESHOLD = 0.8


class ContextCompressor:
    """上下文压缩器，用于管理对话历史的自动压缩"""

    def __init__(
        self,
        llm_client: "BaseLLMClient",
        token_counter: TokenCounter,
        keep_recent: int = DEFAULT_KEEP_RECENT
    ):
        """
        初始化上下文压缩器

        Args:
            llm_client: LLM 客户端，用于生成摘要
            token_counter: Token 计数器
            keep_recent: 保留最近的消息数量（不压缩）
        """
        self.llm_client = llm_client
        self.token_counter = token_counter
        self.keep_recent = keep_recent
        self.threshold = token_counter.get_compression_threshold(COMPRESSION_THRESHOLD)

    def needs_compression(self, system_prompt: str, history: List[Dict[str, Any]]) -> bool:
        """
        检查是否需要压缩上下文

        Args:
            system_prompt: 系统提示词
            history: 对话历史

        Returns:
            如果需要压缩返回 True
        """
        # 计算当前总 token 数
        total_tokens = self.token_counter.count_tokens(system_prompt)
        total_tokens += self.token_counter.count_messages_tokens(history)

        needs = total_tokens >= self.threshold

        if needs:
            logger.info(
                f"Context compression needed: {total_tokens} tokens >= {self.threshold} threshold"
            )

        return needs

    def compress(
        self,
        system_prompt: str,
        history: List[Dict[str, Any]],
        language: str = "en"
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        压缩对话历史

        Args:
            system_prompt: 系统提示词
            history: 对话历史
            language: 语言（用于生成摘要）

        Returns:
            (compressed_history, compression_info)
            - compressed_history: 压缩后的历史（摘要 + 最近消息）
            - compression_info: 压缩信息字典
        """
        # 如果消息数量不足，不需要压缩
        if len(history) <= self.keep_recent:
            return history, {"compressed": False, "reason": "not_enough_messages"}

        # 分离需要压缩的消息和保留的消息
        # 确保截断点不会拆开 tool_call / tool_response 对
        split = len(history) - self.keep_recent
        # 如果 recent 部分以 tool 消息开头，说明它的 tool_call 被留在了
        # to_compress 侧，需要向前扩展 recent 直到包含对应的 assistant 消息
        while split > 0 and history[split].get("role") == "tool":
            split -= 1
        if split <= 0:
            return history, {"compressed": False, "reason": "cannot_find_safe_split"}
        to_compress = history[:split]
        recent = history[split:]

        # 计算压缩前的 token 数
        original_tokens = self.token_counter.count_messages_tokens(to_compress)

        # 生成摘要
        try:
            summary = self._generate_summary(to_compress, language)
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}, skipping compression")
            return history, {"compressed": False, "reason": "summary_generation_failed"}

        # 创建摘要消息
        summary_msg = {
            "role": "assistant",
            "content": summary,
            "_is_summary": True  # 标记这是一条摘要消息
        }

        # 计算压缩后的 token 数
        compressed_tokens = self.token_counter.count_tokens(summary)

        # 构建压缩信息
        compression_info = {
            "compressed": True,
            "messages_compressed": len(to_compress),
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "compression_ratio": round(compressed_tokens / original_tokens, 2) if original_tokens > 0 else 0
        }

        logger.info(
            f"Context compressed: {len(to_compress)} messages, "
            f"{original_tokens} -> {compressed_tokens} tokens "
            f"(ratio: {compression_info['compression_ratio']})"
        )

        return [summary_msg] + recent, compression_info

    def _generate_summary(self, messages: List[Dict[str, Any]], language: str) -> str:
        """
        使用 LLM 生成对话摘要

        Args:
            messages: 要压缩的消息列表
            language: 语言

        Returns:
            摘要文本
        """
        prompt = self._get_summary_prompt(language)
        formatted_messages = self._format_messages_for_summary(messages)

        # 调用 LLM 生成摘要
        response = self.llm_client.chat(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": formatted_messages}
            ],
            tools=None
        )

        content = response.get("content", "")
        if content:
            return content

        # 如果 LLM 返回空，使用 fallback
        return self._fallback_summary(messages, language)

    def _get_summary_prompt(self, language: str) -> str:
        """获取摘要生成的系统提示"""
        if language == "zh":
            return """你是一个对话摘要生成器。请将以下数据库助手对话总结成简洁的摘要。

重点包括：
1. 用户执行的数据库操作（创建表、查询、插入数据等）
2. 发现的重要信息（表结构、数据内容、性能问题等）
3. 遇到的问题及解决方案
4. 关键的上下文信息（表名、列名、数据关系等）

摘要要求：
- 使用简洁的中文
- 保留关键的技术细节（表名、SQL语句要点等）
- 总结控制在500字以内
- 以 "[对话历史摘要]" 开头"""
        else:
            return """You are a conversation summary generator. Please summarize the following database assistant conversation into a concise summary.

Focus on:
1. Database operations performed (create tables, queries, inserts, etc.)
2. Important findings (table structures, data content, performance issues, etc.)
3. Issues encountered and resolutions
4. Key context information (table names, column names, data relationships, etc.)

Summary requirements:
- Use concise language
- Preserve key technical details (table names, SQL statement highlights, etc.)
- Keep under 500 words
- Start with "[Conversation History Summary]" """

    def _format_messages_for_summary(self, messages: List[Dict[str, Any]]) -> str:
        """将消息格式化为适合摘要的文本"""
        lines = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                if content:
                    # 截断过长的内容
                    if len(content) > 1000:
                        content = content[:1000] + "..."
                    lines.append(f"Assistant: {content}")
                # 如果有 tool_calls，简要记录
                tool_calls = msg.get("tool_calls")
                if tool_calls:
                    if isinstance(tool_calls, str):
                        try:
                            tool_calls = json.loads(tool_calls)
                        except Exception:
                            pass
                    if isinstance(tool_calls, list):
                        for tc in tool_calls:
                            if isinstance(tc, dict):
                                func = tc.get("function", {})
                                name = func.get("name", "unknown")
                                lines.append(f"  [Tool call: {name}]")
            elif role == "tool":
                # 工具结果只保留关键信息
                if content:
                    try:
                        result = json.loads(content)
                        status = result.get("status", "")
                        if status == "success":
                            # 简要显示成功结果
                            if len(content) > 500:
                                lines.append(f"  [Tool result: success, truncated]")
                            else:
                                lines.append(f"  [Tool result: {content[:300]}...]")
                        elif status == "error":
                            error = result.get("error", "unknown error")
                            lines.append(f"  [Tool error: {error}]")
                    except Exception:
                        if len(content) > 300:
                            lines.append(f"  [Tool result: {content[:300]}...]")
                        else:
                            lines.append(f"  [Tool result: {content}]")

        return "\n".join(lines)

    def _fallback_summary(self, messages: List[Dict[str, Any]], language: str) -> str:
        """当 LLM 摘要失败时的 fallback 摘要"""
        user_count = len([m for m in messages if m.get("role") == "user"])
        assistant_count = len([m for m in messages if m.get("role") == "assistant"])
        tool_count = len([m for m in messages if m.get("role") == "tool"])

        if language == "zh":
            return (
                f"[对话历史摘要] 之前的对话包含 {user_count} 条用户消息、"
                f"{assistant_count} 条助手响应、{tool_count} 条工具调用结果。"
                f"由于无法生成详细摘要，历史对话已被压缩。"
            )
        else:
            return (
                f"[Conversation History Summary] Previous conversation contained "
                f"{user_count} user messages, {assistant_count} assistant responses, "
                f"and {tool_count} tool results. "
                f"Detailed summary unavailable, history has been compressed."
            )
