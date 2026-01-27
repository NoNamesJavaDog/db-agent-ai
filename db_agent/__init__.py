"""
DB Agent - Database Management AI Agent

A modular AI-powered database management tool supporting multiple LLM providers.
Supports PostgreSQL and MySQL databases.
"""
from db_agent.core import SQLTuningAgent, BaseDatabaseTools, DatabaseToolsFactory
from db_agent.llm import BaseLLMClient, LLMClientFactory
from db_agent.i18n import i18n, t

__version__ = "1.0.0"
__all__ = [
    'SQLTuningAgent',
    'BaseDatabaseTools',
    'DatabaseToolsFactory',
    'BaseLLMClient',
    'LLMClientFactory',
    'i18n',
    't'
]
