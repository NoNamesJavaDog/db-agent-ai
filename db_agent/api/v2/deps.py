"""
Application state and dependency injection for v2 API.
"""
import logging
import time
from typing import Dict, Optional

from db_agent.storage import SQLiteStorage, AuditService
from db_agent.storage.encryption import decrypt
from db_agent.core import SQLTuningAgent
from db_agent.llm import LLMClientFactory
from db_agent.mcp import MCPManager
from db_agent.skills import SkillRegistry

logger = logging.getLogger(__name__)

# Agent cache TTL in seconds (30 minutes)
AGENT_CACHE_TTL = 1800


class CachedAgent:
    """Wrapper that tracks last access time for TTL eviction."""

    def __init__(self, agent: SQLTuningAgent):
        self.agent = agent
        self.last_access = time.time()

    def touch(self):
        self.last_access = time.time()

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.last_access) > AGENT_CACHE_TTL


class AppState:
    """
    Singleton application state shared across all v2 API routes.

    Holds references to storage, MCP manager, skill registry,
    and a cache of SQLTuningAgent instances keyed by session_id.
    """

    def __init__(self):
        self.storage = SQLiteStorage()
        self.mcp_manager = MCPManager(storage=self.storage)
        self.skill_registry = SkillRegistry()
        self.audit_service = AuditService(self.storage)
        self._agents: Dict[int, CachedAgent] = {}

        # Load skills on startup
        try:
            self.skill_registry.load()
            logger.info(f"Loaded {self.skill_registry.count} skills")
        except Exception as e:
            logger.warning(f"Failed to load skills: {e}")

        # Load MCP servers on startup
        try:
            self.mcp_manager.load_servers_sync()
            logger.info("MCP servers loaded")
        except Exception as e:
            logger.warning(f"Failed to load MCP servers: {e}")

    def get_or_create_agent(self, session_id: int) -> SQLTuningAgent:
        """
        Get an agent for the given session, creating one if not cached.

        Reads connection and provider config from SQLiteStorage to build
        the agent on cache miss.
        """
        # Check cache
        cached = self._agents.get(session_id)
        if cached and not cached.is_expired:
            cached.touch()
            return cached.agent

        # Cache miss: build agent from storage
        session = self.storage.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        connection = None
        if session.connection_id:
            connection = self.storage.get_connection_by_id(session.connection_id)

        provider = None
        if session.provider_id:
            provider = self.storage.get_provider_by_id(session.provider_id)

        if not connection:
            connection = self.storage.get_active_connection()
        if not provider:
            provider = self.storage.get_default_provider()

        if not connection:
            raise ValueError("No database connection configured")
        if not provider:
            raise ValueError("No LLM provider configured")

        # Build db_config
        db_config = {
            "type": connection.db_type,
            "host": connection.host,
            "port": connection.port,
            "database": connection.database,
            "user": connection.username,
            "password": decrypt(connection.password_encrypted),
        }

        # Create LLM client
        api_key = decrypt(provider.api_key_encrypted)
        llm_client = LLMClientFactory.create(
            provider=provider.provider,
            api_key=api_key,
            model=provider.model,
            base_url=provider.base_url,
        )

        # Build language preference
        language = self.storage.get_preference("language") or "zh"

        # Create agent
        agent = SQLTuningAgent(
            llm_client=llm_client,
            db_config=db_config,
            language=language,
            storage=self.storage,
            session_id=session_id,
            mcp_manager=self.mcp_manager,
        )
        agent.set_connection_id(connection.id)
        agent.skill_registry = self.skill_registry
        agent.refresh_system_prompt()

        # Restore conversation history
        agent.set_session(session_id, restore_history=True)

        # Cache it
        self._agents[session_id] = CachedAgent(agent)
        logger.info(f"Created agent for session {session_id}")

        return agent

    def evict_agent(self, session_id: int):
        """Remove an agent from cache."""
        self._agents.pop(session_id, None)

    def cleanup_expired(self):
        """Remove all expired agents from cache."""
        expired = [sid for sid, ca in self._agents.items() if ca.is_expired]
        for sid in expired:
            del self._agents[sid]
            logger.info(f"Evicted expired agent for session {sid}")

    async def shutdown(self):
        """Cleanup on application shutdown."""
        self._agents.clear()
        try:
            self.mcp_manager.close_all_sync()
        except Exception as e:
            logger.warning(f"Error closing MCP connections: {e}")


# Global singleton
_app_state: Optional[AppState] = None


def get_app_state() -> AppState:
    """Get or create the global AppState singleton."""
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state
