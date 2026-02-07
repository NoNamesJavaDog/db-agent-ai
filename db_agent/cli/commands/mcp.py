"""
MCP Server Management Commands Mixin

Provides methods for managing MCP (Model Context Protocol) servers:
show, add, remove, enable/disable, show tools.
"""
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich import box

from db_agent.cli.ui import console, SYM_CHECK, SYM_CROSS
from db_agent.i18n import t


class MCPCommandsMixin:
    """Mixin for MCP server management commands.

    Expects the host class to provide:
        self.storage - SQLiteStorage instance
        self.agent   - SQLTuningAgent instance
    """

    def handle_mcp_command(self, args: str):
        """Handle /mcp sub-commands"""
        parts = args.strip().split(maxsplit=1)
        if not parts:
            self.show_mcp_servers()
            return

        subcommand = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else None

        if subcommand == "list":
            self.show_mcp_servers()
        elif subcommand == "add":
            self.add_mcp_server_wizard()
        elif subcommand == "remove":
            if arg:
                self.remove_mcp_server(arg)
            else:
                console.print(f"[red]{t('error')}:[/] /mcp remove <name>")
        elif subcommand == "enable":
            if arg:
                self.enable_mcp_server(arg, True)
            else:
                console.print(f"[red]{t('error')}:[/] /mcp enable <name>")
        elif subcommand == "disable":
            if arg:
                self.enable_mcp_server(arg, False)
            else:
                console.print(f"[red]{t('error')}:[/] /mcp disable <name>")
        elif subcommand == "tools":
            self.show_mcp_tools(arg)
        else:
            console.print(f"[red]{t('invalid_choice')}[/]")

    def show_mcp_servers(self):
        """Show MCP Server list"""
        console.print()
        servers = self.storage.list_mcp_servers()

        if not servers:
            console.print(f"[dim]{t('mcp_servers_empty')}[/]")
            console.print()
            console.print(f"[dim]Commands: /mcp add | /mcp tools[/]")
            console.print()
            return

        table = Table(box=box.ROUNDED, padding=(0, 2))
        table.add_column("#", style="cyan", justify="center", width=3)
        table.add_column(t("mcp_server_name"), style="white")
        table.add_column(t("mcp_server_command"), style="dim")
        table.add_column(t("mcp_server_status"), style="white")

        for i, server in enumerate(servers, 1):
            status = f"[green]{t('mcp_enabled')}[/]" if server.get('enabled') else f"[dim]{t('mcp_disabled')}[/]"
            command = f"{server['command']} {' '.join(server.get('args', [])[:2])}..."
            if len(command) > 40:
                command = command[:40] + "..."
            table.add_row(
                str(i),
                server['name'],
                command,
                status
            )

        console.print(Panel(
            table,
            title=f"[bold cyan]{t('mcp_servers_title')}[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        # Show sub-commands
        console.print()
        console.print(f"[dim]Commands: /mcp add | /mcp remove <name> | /mcp enable <name> | /mcp disable <name> | /mcp tools[/]")
        console.print()

    def add_mcp_server_wizard(self):
        """Wizard for adding a new MCP Server"""
        import json as _json
        from datetime import datetime
        from db_agent.storage.models import MCPServer

        console.print()
        console.print(f"[bold cyan]{t('mcp_add_server')}[/]")
        console.print()

        # Server name
        name = Prompt.ask(f"[cyan]{t('mcp_server_name')}[/]")
        if not name:
            console.print(f"[dim]{t('cancelled')}[/]")
            return

        # Check if name exists
        existing = self.storage.get_mcp_server(name)
        if existing:
            console.print(f"[red]{t('mcp_server_exists', name=name)}[/]")
            return

        # Command
        console.print()
        console.print(f"[dim]{t('mcp_command_hint')}[/]")
        command = Prompt.ask(f"[cyan]{t('mcp_command')}[/]", default="npx")

        # Arguments
        console.print()
        console.print(f"[dim]{t('mcp_args_hint')}[/]")
        args_str = Prompt.ask(f"[cyan]{t('mcp_args')}[/]", default="")
        args = args_str.split() if args_str else []

        # Environment variables (optional)
        console.print()
        console.print(f"[dim]{t('mcp_env_hint')}[/]")
        env_str = Prompt.ask(f"[cyan]{t('mcp_env')}[/]", default="")
        env = None
        if env_str:
            try:
                # Parse KEY=VALUE pairs
                env = {}
                for pair in env_str.split():
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        env[k] = v
            except Exception:
                console.print(f"[yellow]{t('mcp_env_parse_error')}[/]")

        # Save server config
        now = datetime.now()
        server = MCPServer(
            id=None,
            name=name,
            command=command,
            args=_json.dumps(args),
            env=_json.dumps(env) if env else None,
            enabled=True,
            created_at=now,
            updated_at=now
        )

        try:
            self.storage.add_mcp_server(server)
            console.print(f"[green]{SYM_CHECK()}[/] {t('mcp_server_added', name=name)}")

            # Try to connect
            console.print()
            if Confirm.ask(f"[cyan]{t('mcp_connect_now')}[/]", default=True):
                self._connect_mcp_server(name)

        except Exception as e:
            console.print(f"[red]{t('error')}:[/] {e}")

        console.print()

    def remove_mcp_server(self, name: str):
        """Remove an MCP Server"""
        server = self.storage.get_mcp_server(name)
        if not server:
            console.print(f"[red]{t('mcp_server_not_found', name=name)}[/]")
            return

        if Confirm.ask(f"[yellow]{t('mcp_server_delete_confirm', name=name)}[/]", default=False):
            # Disconnect if connected
            if hasattr(self.agent, 'mcp_manager') and self.agent.mcp_manager:
                if name in self.agent.mcp_manager:
                    self.agent.mcp_manager.remove_server_sync(name)
                    # Refresh system prompt to remove MCP tools descriptions
                    self.agent.refresh_system_prompt()

            self.storage.delete_mcp_server(name)
            console.print(f"[green]{SYM_CHECK()}[/] {t('mcp_server_deleted', name=name)}")

    def enable_mcp_server(self, name: str, enabled: bool):
        """Enable/disable an MCP Server"""
        server = self.storage.get_mcp_server(name)
        if not server:
            console.print(f"[red]{t('mcp_server_not_found', name=name)}[/]")
            return

        self.storage.enable_mcp_server(name, enabled)

        if enabled:
            console.print(f"[green]{SYM_CHECK()}[/] {t('mcp_server_enabled', name=name)}")
            # Try to connect
            self._connect_mcp_server(name)
        else:
            console.print(f"[green]{SYM_CHECK()}[/] {t('mcp_server_disabled', name=name)}")
            # Disconnect if connected
            if hasattr(self.agent, 'mcp_manager') and self.agent.mcp_manager:
                if name in self.agent.mcp_manager:
                    self.agent.mcp_manager.remove_server_sync(name)
                    # Refresh system prompt to remove MCP tools descriptions
                    self.agent.refresh_system_prompt()

    def _connect_mcp_server(self, name: str):
        """Connect to an MCP Server"""
        import json as _json
        from db_agent.mcp import MCPServerConfig, MCPManager

        server_data = None
        for s in self.storage.list_mcp_servers():
            if s['name'] == name:
                server_data = s
                break

        if not server_data:
            console.print(f"[red]{t('mcp_server_not_found', name=name)}[/]")
            return

        config = MCPServerConfig(
            name=server_data['name'],
            command=server_data['command'],
            args=server_data.get('args', []),
            env=server_data.get('env'),
            enabled=True
        )

        # Ensure MCP manager exists
        if not hasattr(self.agent, 'mcp_manager') or self.agent.mcp_manager is None:
            self.agent.mcp_manager = MCPManager(self.storage)

        with console.status(f"[dim]{t('mcp_connecting', name=name)}[/]", spinner="dots"):
            try:
                success = self.agent.mcp_manager.add_server_sync(config)
                if success:
                    tools = self.agent.mcp_manager.get_server_tools(name)
                    # Refresh system prompt to include new MCP tools descriptions
                    self.agent.refresh_system_prompt()
                    console.print(f"[green]{SYM_CHECK()}[/] {t('mcp_connected', name=name, tools=len(tools))}")
                else:
                    console.print(f"[red]{SYM_CROSS()}[/] {t('mcp_connect_failed', name=name)}")
            except Exception as e:
                console.print(f"[red]{SYM_CROSS()}[/] {t('mcp_connect_failed', name=name)}: {e}")

    def show_mcp_tools(self, server_name: str = None):
        """Show MCP tools list"""
        console.print()

        if not hasattr(self.agent, 'mcp_manager') or not self.agent.mcp_manager:
            console.print(f"[dim]{t('mcp_no_connected_servers')}[/]")
            console.print()
            return

        if server_name:
            # Show tools from specific server
            tools = self.agent.mcp_manager.get_server_tools(server_name)
            if not tools:
                console.print(f"[dim]{t('mcp_no_tools', server=server_name)}[/]")
                return

            self._display_tools_table(tools, server_name)
        else:
            # Show all tools from all servers
            all_tools = self.agent.mcp_manager.get_all_tools()
            if not all_tools:
                console.print(f"[dim]{t('mcp_no_tools_available')}[/]")
                console.print()
                return

            self._display_tools_table(all_tools, None)

    def _display_tools_table(self, tools: list, server_name: str = None):
        """Display tools table"""
        table = Table(box=box.ROUNDED, padding=(0, 2))
        table.add_column("#", style="cyan", justify="center", width=3)
        table.add_column(t("mcp_tool_name"), style="green")
        table.add_column(t("mcp_tool_description"), style="white")

        for i, tool in enumerate(tools, 1):
            func = tool.get('function', {})
            name = func.get('name', 'unknown')
            desc = func.get('description', '')
            if len(desc) > 60:
                desc = desc[:60] + "..."
            table.add_row(str(i), name, desc)

        title = f"{t('mcp_tools_title')}"
        if server_name:
            title += f" ({server_name})"

        console.print(Panel(
            table,
            title=f"[bold cyan]{title}[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))
        console.print()
