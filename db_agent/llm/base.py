"""
LLM Client Base Class
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseLLMClient(ABC):
    """LLM客户端基类"""

    @abstractmethod
    def chat(self, messages: List[Dict], tools: List[Dict] = None) -> Dict[str, Any]:
        """发送聊天请求"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """获取模型名称"""
        pass
