"""
LLM Client Factory
"""
from typing import Dict
from db_agent.i18n import t
from .base import BaseLLMClient
from .openai_compatible import OpenAICompatibleClient
from .claude import ClaudeClient
from .gemini import GeminiClient


class LLMClientFactory:
    """LLM客户端工厂"""

    PROVIDERS = {
        "openai": {
            "name": "OpenAI/ChatGPT",
            "base_url": "https://api.openai.com/v1",
            "default_model": "gpt-4o"
        },
        "deepseek": {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com",
            "default_model": "deepseek-chat"
        },
        "claude": {
            "name": "Claude",
            "base_url": None,
            "default_model": "claude-sonnet-4-20250514"
        },
        "gemini": {
            "name": "Gemini",
            "base_url": None,
            "default_model": "gemini-pro"
        },
        "qwen": {
            "name": "Qwen/通义千问",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_model": "qwen-turbo"
        },
        "ollama": {
            "name": "Ollama (本地)",
            "base_url": "http://localhost:11434/v1",
            "default_model": "llama2"
        }
    }

    @classmethod
    def create(cls, provider: str, api_key: str, model: str = None, base_url: str = None) -> BaseLLMClient:
        """创建LLM客户端"""
        provider = provider.lower()

        if provider not in cls.PROVIDERS:
            raise ValueError(t("db_unsupported_provider", provider=provider))

        info = cls.PROVIDERS[provider]
        model = model or info["default_model"]
        base_url = base_url or info["base_url"]

        if provider == "claude":
            return ClaudeClient(api_key=api_key, model=model)
        elif provider == "gemini":
            return GeminiClient(api_key=api_key, model=model)
        else:
            # OpenAI 兼容的提供商
            return OpenAICompatibleClient(
                api_key=api_key,
                base_url=base_url,
                model=model,
                provider_name=info["name"]
            )

    @classmethod
    def get_available_providers(cls) -> Dict[str, str]:
        """获取可用的提供商列表"""
        return {k: v["name"] for k, v in cls.PROVIDERS.items()}
