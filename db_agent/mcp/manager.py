"""
MCP Connection Manager

Manages multiple MCP client connections, providing a unified interface
for the agent to interact with external MCP servers.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .config import MCPServerConfig
from .client import MCPClient

if TYPE_CHECKING:
    from db_agent.storage import SQLiteStorage

logger = logging.getLogger(__name__)


class MCPManager:
    """
    Manages multiple MCP client connections.

    Provides methods to:
    - Load and connect to configured MCP servers
    - Get aggregated tool lists from all servers
    - Route tool calls to the appropriate server
    - Handle connection lifecycle

    Example:
        manager = MCPManager(storage)
        await manager.load_servers()
        tools = manager.get_all_tools()  # Returns tools from all connected servers
        result = await manager.call_tool("mcp_filesystem_read_file", {"path": "/tmp/test.txt"})
    """

    def __init__(self, storage: Optional["SQLiteStorage"] = None):
        """
        Initialize MCP Manager.

        Args:
            storage: SQLite storage for loading MCP server configs
        """
        self.storage = storage
        self.clients: Dict[str, MCPClient] = {}
        self._all_tools: List[Dict] = []
        self._tool_map: Dict[str, str] = {}  # Maps tool name to server name
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    async def load_servers(self) -> None:
        """
        Load and connect to all enabled MCP servers from storage.
        """
        if not self.storage:
            logger.warning("No storage provided, cannot load MCP servers")
            return

        try:
            servers = self.storage.list_mcp_servers()
            for server in servers:
                if server.get('enabled', True):
                    config = MCPServerConfig(
                        name=server['name'],
                        command=server['command'],
                        args=server.get('args', []),
                        env=server.get('env'),
                        enabled=True
                    )
                    await self.add_server(config)
        except Exception as e:
            logger.error(f"Failed to load MCP servers: {e}")

    def load_servers_sync(self) -> None:
        """Synchronous wrapper for load_servers."""
        loop = self._get_loop()
        loop.run_until_complete(self.load_servers())

    async def add_server(self, config: MCPServerConfig) -> bool:
        """
        Add and connect to an MCP server.

        Args:
            config: MCP server configuration

        Returns:
            True if connection successful
        """
        if config.name in self.clients:
            logger.warning(f"MCP server {config.name} already exists, skipping")
            return False

        try:
            client = MCPClient(config)
            await client.connect()

            # Get tools from this server
            tools = await client.list_tools()

            self.clients[config.name] = client

            # Update tool map and aggregated tools
            for tool in tools:
                tool_name = tool['function']['name']
                self._tool_map[tool_name] = config.name
                self._all_tools.append(tool)

            logger.info(f"MCP server {config.name} added with {len(tools)} tools")
            return True

        except Exception as e:
            logger.error(f"Failed to add MCP server {config.name}: {e}")
            return False

    def add_server_sync(self, config: MCPServerConfig) -> bool:
        """Synchronous wrapper for add_server."""
        loop = self._get_loop()
        return loop.run_until_complete(self.add_server(config))

    async def remove_server(self, name: str) -> bool:
        """
        Remove and disconnect an MCP server.

        Args:
            name: Server name

        Returns:
            True if removal successful
        """
        if name not in self.clients:
            logger.warning(f"MCP server {name} not found")
            return False

        try:
            client = self.clients[name]
            await client.close()

            # Remove tools from this server
            tools_to_remove = [
                tool_name for tool_name, server_name in self._tool_map.items()
                if server_name == name
            ]
            for tool_name in tools_to_remove:
                del self._tool_map[tool_name]

            self._all_tools = [
                tool for tool in self._all_tools
                if tool['function']['name'] not in tools_to_remove
            ]

            del self.clients[name]
            logger.info(f"MCP server {name} removed")
            return True

        except Exception as e:
            logger.error(f"Failed to remove MCP server {name}: {e}")
            return False

    def remove_server_sync(self, name: str) -> bool:
        """Synchronous wrapper for remove_server."""
        loop = self._get_loop()
        return loop.run_until_complete(self.remove_server(name))

    def get_all_tools(self) -> List[Dict]:
        """
        Get all tools from all connected MCP servers.

        Returns:
            List of tool definitions in OpenAI function format
        """
        return self._all_tools.copy()

    def get_server_tools(self, server_name: str) -> List[Dict]:
        """
        Get tools from a specific MCP server.

        Args:
            server_name: Name of the server

        Returns:
            List of tool definitions
        """
        if server_name not in self.clients:
            return []

        return self.clients[server_name].get_tools()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """
        Call an MCP tool by its full name.

        The tool name should be in format: mcp_{server_name}_{actual_tool_name}

        Args:
            tool_name: Full tool name (e.g., "mcp_filesystem_read_file")
            arguments: Tool arguments

        Returns:
            Tool result dictionary
        """
        # Parse tool name to extract server and actual tool
        if not tool_name.startswith("mcp_"):
            return {
                "status": "error",
                "error": f"Invalid MCP tool name: {tool_name}"
            }

        # Find which server this tool belongs to
        if tool_name not in self._tool_map:
            return {
                "status": "error",
                "error": f"Unknown MCP tool: {tool_name}"
            }

        server_name = self._tool_map[tool_name]
        if server_name not in self.clients:
            return {
                "status": "error",
                "error": f"MCP server not connected: {server_name}"
            }

        # Extract actual tool name (remove mcp_{server_name}_ prefix)
        prefix = f"mcp_{server_name}_"
        actual_tool_name = tool_name[len(prefix):]

        # Call the tool
        client = self.clients[server_name]
        return await client.call_tool(actual_tool_name, arguments)

    def call_tool_sync(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """Synchronous wrapper for call_tool."""
        loop = self._get_loop()
        return loop.run_until_complete(self.call_tool(tool_name, arguments))

    async def close_all(self) -> None:
        """Close all MCP server connections."""
        for name, client in list(self.clients.items()):
            try:
                await client.close()
            except Exception as e:
                logger.warning(f"Error closing MCP server {name}: {e}")

        self.clients.clear()
        self._all_tools.clear()
        self._tool_map.clear()

    def close_all_sync(self) -> None:
        """Synchronous wrapper for close_all."""
        loop = self._get_loop()
        loop.run_until_complete(self.close_all())

    def list_connected_servers(self) -> List[str]:
        """
        Get list of connected server names.

        Returns:
            List of server names
        """
        return list(self.clients.keys())

    def get_server_status(self, name: str) -> Dict:
        """
        Get status of a specific server.

        Args:
            name: Server name

        Returns:
            Status dictionary with connection info and tool count
        """
        if name not in self.clients:
            return {
                "name": name,
                "connected": False,
                "tool_count": 0
            }

        client = self.clients[name]
        return {
            "name": name,
            "connected": client.is_connected,
            "tool_count": len(client.get_tools())
        }

    def get_all_server_status(self) -> List[Dict]:
        """
        Get status of all servers.

        Returns:
            List of status dictionaries
        """
        return [self.get_server_status(name) for name in self.clients.keys()]

    def is_mcp_tool(self, tool_name: str) -> bool:
        """
        Check if a tool name is an MCP tool.

        Args:
            tool_name: Tool name to check

        Returns:
            True if it's an MCP tool
        """
        return tool_name.startswith("mcp_") and tool_name in self._tool_map

    def __len__(self) -> int:
        """Return number of connected servers."""
        return len(self.clients)

    def __contains__(self, name: str) -> bool:
        """Check if a server is connected."""
        return name in self.clients

    def get_tools_prompt(self) -> str:
        """
        Generate MCP tools description text for system prompt.

        Returns:
            Formatted string describing available MCP tools for AI to use
        """
        tools = self.get_all_tools()
        if not tools:
            return ""

        lines = ["## External Tools (MCP)", ""]
        lines.append("The following external tools are available via MCP servers:")
        lines.append("")

        for tool in tools:
            name = tool['function']['name']
            desc = tool['function'].get('description', f'MCP tool: {name}')
            lines.append(f"- **{name}**: {desc}")

        return "\n".join(lines)
