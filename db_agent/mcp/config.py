"""
MCP Configuration Management

Provides configuration dataclasses for MCP server connections.
Compatible with Claude Desktop's mcpServers configuration format.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json


@dataclass
class MCPServerConfig:
    """
    MCP Server configuration.

    Compatible with Claude Desktop's configuration format:
    {
      "mcpServers": {
        "filesystem": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
        },
        "github": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-github"],
          "env": {"GITHUB_TOKEN": "xxx"}
        }
      }
    }

    Attributes:
        name: Server name (unique identifier)
        command: Command to start the server (e.g., "npx", "python", "node")
        args: Command arguments
        env: Optional environment variables
        enabled: Whether this server is enabled
    """
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Optional[Dict[str, str]] = None
    enabled: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'command': self.command,
            'args': self.args,
            'env': self.env,
            'enabled': self.enabled
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MCPServerConfig':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            command=data['command'],
            args=data.get('args', []),
            env=data.get('env'),
            enabled=data.get('enabled', True)
        )

    def to_claude_desktop_format(self) -> dict:
        """
        Convert to Claude Desktop mcpServers format.

        Returns dict like:
        {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        }
        """
        result = {
            'command': self.command,
            'args': self.args
        }
        if self.env:
            result['env'] = self.env
        return result

    @classmethod
    def from_claude_desktop_format(cls, name: str, config: dict) -> 'MCPServerConfig':
        """
        Create from Claude Desktop mcpServers format.

        Args:
            name: Server name (the key in mcpServers dict)
            config: The config dict with command, args, env
        """
        return cls(
            name=name,
            command=config['command'],
            args=config.get('args', []),
            env=config.get('env'),
            enabled=True
        )


def load_claude_desktop_config(config_path: str) -> Dict[str, MCPServerConfig]:
    """
    Load MCP servers from Claude Desktop config file.

    Args:
        config_path: Path to Claude Desktop config file (usually ~/Library/Application Support/Claude/claude_desktop_config.json)

    Returns:
        Dict mapping server name to MCPServerConfig
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    servers = {}
    mcp_servers = data.get('mcpServers', {})
    for name, config in mcp_servers.items():
        servers[name] = MCPServerConfig.from_claude_desktop_format(name, config)

    return servers


def save_claude_desktop_config(config_path: str, servers: Dict[str, MCPServerConfig]):
    """
    Save MCP servers to Claude Desktop config format.

    Args:
        config_path: Path to save the config file
        servers: Dict mapping server name to MCPServerConfig
    """
    # Try to load existing config to preserve other settings
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    # Update mcpServers section
    data['mcpServers'] = {
        name: config.to_claude_desktop_format()
        for name, config in servers.items()
        if config.enabled
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
