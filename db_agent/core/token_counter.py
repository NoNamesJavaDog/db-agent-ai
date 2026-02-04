"""Token counting utilities for context management"""
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# 各模型的上下文限制
MODEL_CONTEXT_LIMITS = {
    # Claude
    "claude-sonnet-4-20250514": 200000,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    # OpenAI
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
    # DeepSeek
    "deepseek-chat": 64000,
    "deepseek-coder": 64000,
    # Gemini
    "gemini-pro": 32000,
    "gemini-1.5-pro": 1000000,
    "gemini-1.5-flash": 1000000,
    # Qwen
    "qwen-turbo": 8000,
    "qwen-plus": 32000,
    "qwen-max": 32000,
    # Ollama / Local
    "llama2": 4096,
    "llama3": 8192,
    "llama3.1": 128000,
    "mistral": 8192,
    "mixtral": 32000,
}

DEFAULT_CONTEXT_LIMIT = 8000


class TokenCounter:
    """Token 计数器，用于估算消息的 token 数量"""

    # 类级别的标志，用于避免重复警告
    _tiktoken_warning_logged = False

    def __init__(self, provider: str, model: str):
        """
        初始化 Token 计数器

        Args:
            provider: LLM 提供商名称
            model: 模型名称
        """
        self.provider = provider.lower()
        self.model = model
        self._encoding = None
        self._encoding_loaded = False  # 标记是否已尝试加载

    def _get_encoding(self):
        """获取 tiktoken 编码器（懒加载）"""
        if not self._encoding_loaded:
            self._encoding_loaded = True
            try:
                import tiktoken
                # cl100k_base 是 GPT-4 和 Claude 使用的编码
                self._encoding = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                if not TokenCounter._tiktoken_warning_logged:
                    logger.warning("tiktoken not installed, using fallback token estimation")
                    TokenCounter._tiktoken_warning_logged = True
            except Exception as e:
                if not TokenCounter._tiktoken_warning_logged:
                    logger.warning(f"Failed to load tiktoken encoding: {e}")
                    TokenCounter._tiktoken_warning_logged = True
        return self._encoding

    def count_tokens(self, text: str) -> int:
        """
        计算文本的 token 数量

        Args:
            text: 要计数的文本

        Returns:
            估算的 token 数量
        """
        if not text:
            return 0

        encoding = self._get_encoding()
        if encoding:
            try:
                return len(encoding.encode(text))
            except Exception as e:
                logger.debug(f"tiktoken encoding failed: {e}")

        # Fallback: 粗略估算（约 4 字符 = 1 token）
        return len(text) // 4

    def count_messages_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        计算消息列表的 token 数量

        Args:
            messages: 消息列表

        Returns:
            估算的总 token 数量
        """
        total = 0
        for msg in messages:
            # 计算消息内容的 token
            content = msg.get("content")
            if content:
                total += self.count_tokens(content)

            # 计算 tool_calls 的 token
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                try:
                    if isinstance(tool_calls, str):
                        total += self.count_tokens(tool_calls)
                    else:
                        total += self.count_tokens(json.dumps(tool_calls, ensure_ascii=False))
                except Exception:
                    pass

            # 每条消息的元数据开销（role, 分隔符等）
            total += 4

        return total

    def get_context_limit(self) -> int:
        """
        获取当前模型的上下文限制

        Returns:
            上下文 token 限制
        """
        # 精确匹配
        if self.model in MODEL_CONTEXT_LIMITS:
            return MODEL_CONTEXT_LIMITS[self.model]

        # 前缀匹配
        for prefix, limit in MODEL_CONTEXT_LIMITS.items():
            if self.model.startswith(prefix):
                return limit

        # 根据提供商猜测默认值
        provider_defaults = {
            "anthropic": 200000,
            "claude": 200000,
            "openai": 128000,
            "deepseek": 64000,
            "google": 32000,
            "gemini": 32000,
            "qwen": 32000,
            "ollama": 8192,
        }

        for provider_key, limit in provider_defaults.items():
            if provider_key in self.provider.lower():
                return limit

        return DEFAULT_CONTEXT_LIMIT

    def get_compression_threshold(self, percent: float = 0.8) -> int:
        """
        获取触发压缩的 token 阈值

        Args:
            percent: 触发压缩的上下文使用百分比（默认 80%）

        Returns:
            触发压缩的 token 数量阈值
        """
        return int(self.get_context_limit() * percent)
