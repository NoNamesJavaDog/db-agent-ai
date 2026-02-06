"""
MCP Client Implementation

Wraps the MCP SDK to provide a simplified interface for connecting to
external MCP servers and calling their tools.
"""

import asyncio
import logging
import subprocess
import sys
from typing import Any, Dict, List, Optional

from .config import MCPServerConfig

logger = logging.getLogger(__name__)


class MCPClient:
    """
    MCP Client for connecting to external MCP servers.

    Uses the official MCP Python SDK (mcp package) to communicate with
    servers via stdio transport.

    Example:
        config = MCPServerConfig(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        )
        async with MCPClient(config) as client:
            tools = await client.list_tools()
            result = await client.call_tool("read_file", {"path": "/tmp/test.txt"})
    """

    def __init__(self, config: MCPServerConfig):
        """
        Initialize MCP client.

        Args:
            config: MCP server configuration
        """
        self.config = config
        self.name = config.name
        self._session = None
        self._stdio_context = None
        self._session_context = None
        self._tools: List[Dict] = []
        self._connected = False
        self.server_info = None

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected

    async def connect(self) -> None:
        """
        Connect to the MCP server.

        Starts the server process and establishes stdio communication.
        """
        try:
            from mcp import ClientSession
            from mcp.client.stdio import stdio_client, StdioServerParameters

            # Create server parameters
            server_params = StdioServerParameters(
                command=self.config.command,
                args=self.config.args,
                env=self.config.env
            )

            # Create and enter stdio context
            self._stdio_context = stdio_client(server_params)
            read_stream, write_stream = await self._stdio_context.__aenter__()

            # Create and enter session context
            self._session = ClientSession(read_stream, write_stream)
            self._session_context = self._session
            await self._session.__aenter__()

            # Initialize the session
            result = await self._session.initialize()
            self.server_info = {
                "name": result.serverInfo.name if result.serverInfo else self.name,
                "version": result.serverInfo.version if result.serverInfo else "unknown"
            }
            self._connected = True

            logger.info(f"MCP Client connected to server: {self.name}")

        except ImportError as e:
            logger.error(f"MCP SDK not installed. Please install with: pip install mcp[cli]")
            raise ImportError("MCP SDK not installed. Install with: pip install mcp[cli]") from e
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.name}: {e}")
            # Clean up on failure
            await self._cleanup()
            raise ConnectionError(f"Failed to connect to MCP server {self.name}: {e}") from e

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._session_context:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception as e:
                logger.debug(f"Error closing session: {e}")
            self._session_context = None
            self._session = None

        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception as e:
                logger.debug(f"Error closing stdio: {e}")
            self._stdio_context = None

    async def close(self) -> None:
        """Close the connection to the MCP server."""
        await self._cleanup()
        self._connected = False
        logger.info(f"MCP Client disconnected from server: {self.name}")

    async def list_tools(self) -> List[Dict]:
        """
        Get list of tools provided by the server.

        Returns:
            List of tool definitions in OpenAI function format
        """
        if not self._connected:
            raise ConnectionError("Not connected to MCP server")

        try:
            result = await self._session.list_tools()

            # Convert MCP tools to OpenAI function format
            self._tools = []
            for tool in result.tools:
                openai_tool = self._convert_tool_to_openai_format(tool)
                self._tools.append(openai_tool)

            return self._tools

        except Exception as e:
            logger.error(f"Failed to list tools from {self.name}: {e}")
            raise

    def _convert_tool_to_openai_format(self, mcp_tool) -> Dict:
        """
        Convert MCP tool definition to OpenAI function format.

        Args:
            mcp_tool: MCP Tool object

        Returns:
            Tool definition in OpenAI function format
        """
        # MCP tool has: name, description, inputSchema
        return {
            "type": "function",
            "function": {
                "name": f"mcp_{self.name}_{mcp_tool.name}",
                "description": mcp_tool.description or f"MCP tool from {self.name}",
                "parameters": mcp_tool.inputSchema if mcp_tool.inputSchema else {
                    "type": "object",
                    "properties": {}
                }
            }
        }

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool (without mcp_servername_ prefix)
            arguments: Tool arguments

        Returns:
            Tool result as dictionary
        """
        if not self._connected:
            raise ConnectionError("Not connected to MCP server")

        try:
            result = await self._session.call_tool(tool_name, arguments)

            # Process result content
            if result.content:
                # MCP returns content as a list of content blocks
                contents = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        contents.append(content.text)
                    elif hasattr(content, 'data'):
                        contents.append(str(content.data))
                    else:
                        contents.append(str(content))

                return {
                    "status": "success" if not result.isError else "error",
                    "content": "\n".join(contents) if contents else None
                }
            else:
                return {
                    "status": "success",
                    "content": None
                }

        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {self.name}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def get_tools(self) -> List[Dict]:
        """
        Get cached tools list.

        Returns:
            List of tool definitions in OpenAI function format
        """
        return self._tools

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class MCPClientSync:
    """
    Synchronous wrapper for MCPClient.

    Provides synchronous methods for use in non-async contexts.
    Creates and manages its own event loop.
    """

    def __init__(self, config: MCPServerConfig):
        """
        Initialize sync MCP client wrapper.

        Args:
            config: MCP server configuration
        """
        self._client = MCPClient(config)
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

    def connect(self) -> None:
        """Connect to the MCP server."""
        loop = self._get_loop()
        loop.run_until_complete(self._client.connect())

    def close(self) -> None:
        """Close the connection."""
        if self._loop and not self._loop.is_closed():
            self._loop.run_until_complete(self._client.close())

    def list_tools(self) -> List[Dict]:
        """Get list of tools."""
        loop = self._get_loop()
        return loop.run_until_complete(self._client.list_tools())

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """Call a tool."""
        loop = self._get_loop()
        return loop.run_until_complete(self._client.call_tool(tool_name, arguments))

    def get_tools(self) -> List[Dict]:
        """Get cached tools list."""
        return self._client.get_tools()

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._client.is_connected

    @property
    def name(self) -> str:
        """Get server name."""
        return self._client.name
