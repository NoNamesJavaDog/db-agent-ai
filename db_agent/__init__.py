"""
DB Agent - PostgreSQL Database Management AI Agent

A modular AI-powered database management tool supporting multiple LLM providers.
"""
from db_agent.core import SQLTuningAgent, DatabaseTools
from db_agent.llm import BaseLLMClient, LLMClientFactory
from db_agent.i18n import i18n, t

__version__ = "1.0.0"
__all__ = [
    'SQLTuningAgent',
    'DatabaseTools',
    'BaseLLMClient',
    'LLMClientFactory',
    'i18n',
    't'
]
