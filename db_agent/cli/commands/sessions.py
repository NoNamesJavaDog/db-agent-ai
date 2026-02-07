"""
Session Management Commands Mixin

Provides methods for managing chat sessions:
show, create, switch, delete, rename.
"""
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich import box

from db_agent.cli.ui import console, SYM_CHECK
from db_agent.i18n import t


class SessionCommandsMixin:
    """Mixin for session management commands.

    Expects the host class to provide:
        self.storage            - SQLiteStorage instance
        self.agent              - SQLTuningAgent instance
        self.current_session_id - Current session ID
        self.show_history()     - Method to display conversation history
    """

    def show_sessions(self):
        """Show session list"""
        console.print()
        sessions = self.storage.list_sessions()

        if not sessions:
            console.print(f"[dim]{t('sessions_empty')}[/]")
            console.print()
            return

        table = Table(box=box.ROUNDED, padding=(0, 2))
        table.add_column("#", style="cyan", justify="center", width=3)
        table.add_column("ID", style="dim", width=4)
        table.add_column(t("session_name"), style="white")
        table.add_column(t("session_messages"), style="white", justify="right")
        table.add_column(t("session_created"), style="dim")
        table.add_column(t("session_status"), style="white")

        for i, session in enumerate(sessions, 1):
            msg_count = self.storage.get_session_message_count(session.id)
            status = f"[green]{t('session_current')}[/]" if session.is_current else ""
            created = session.created_at.strftime("%Y-%m-%d %H:%M") if session.created_at else ""
            table.add_row(
                str(i),
                str(session.id),
                session.name,
                str(msg_count),
                created,
                status
            )

        console.print(Panel(
            table,
            title=f"[bold cyan]{t('sessions_title')}[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        # Show sub-commands
        console.print()
        console.print(f"[dim]Commands: /session new [name] | /session use <id|name> | /session delete <id|name> | /session rename <name>[/]")
        console.print()

    def handle_session_command(self, args: str):
        """Handle /session sub-commands"""
        parts = args.strip().split(maxsplit=1)
        if not parts:
            self.show_sessions()
            return

        subcommand = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else None

        if subcommand == "new":
            self.create_new_session(arg)
        elif subcommand == "use":
            if arg:
                self.switch_session(arg)
            else:
                console.print(f"[red]{t('error')}:[/] /session use <id|name>")
        elif subcommand == "delete":
            if arg:
                self.delete_session(arg)
            else:
                console.print(f"[red]{t('error')}:[/] /session delete <id|name>")
        elif subcommand == "rename":
            if arg:
                self.rename_current_session(arg)
            else:
                console.print(f"[red]{t('error')}:[/] /session rename <name>")
        else:
            console.print(f"[red]{t('invalid_choice')}[/]")

    def create_new_session(self, name: str = None):
        """Create a new session"""
        from datetime import datetime

        if not name:
            # Generate default name with timestamp
            name = datetime.now().strftime(t("session_default_name_format"))

        # Get current connection and provider
        active_conn = self.storage.get_active_connection()
        default_provider = self.storage.get_default_provider()

        connection_id = active_conn.id if active_conn else None
        provider_id = default_provider.id if default_provider else None

        # Create session
        session_id = self.storage.create_session(name, connection_id, provider_id)
        self.storage.set_current_session(session_id)
        self.current_session_id = session_id

        # Reset agent conversation and set new session
        self.agent.conversation_history = []
        self.agent.session_id = session_id

        console.print(f"[green]{SYM_CHECK()}[/] {t('session_created', name=name)}")

    def switch_session(self, identifier: str):
        """Switch to a specified session"""
        # Try to find by ID first
        session = None
        try:
            session_id = int(identifier)
            session = self.storage.get_session(session_id)
        except ValueError:
            # Try to find by name
            session = self.storage.get_session_by_name(identifier)

        if not session:
            console.print(f"[red]{t('session_not_found', identifier=identifier)}[/]")
            return

        # Check if switching to current session
        if session.is_current:
            console.print(f"[dim]{t('session_already_current', name=session.name)}[/]")
            return

        # Set as current
        self.storage.set_current_session(session.id)
        self.current_session_id = session.id

        # Restore conversation history
        self.agent.conversation_history = []
        self.agent.session_id = session.id
        self.agent._restore_conversation_history()

        msg_count = len(self.agent.conversation_history)
        console.print(f"[green]{SYM_CHECK()}[/] {t('session_switched', name=session.name)}")
        if msg_count > 0:
            console.print(f"[dim]{t('session_restored_messages', count=msg_count)}[/]")
            self.show_history()

    def delete_session(self, identifier: str):
        """Delete a session"""
        # Try to find by ID first
        session = None
        try:
            session_id = int(identifier)
            session = self.storage.get_session(session_id)
        except ValueError:
            # Try to find by name
            session = self.storage.get_session_by_name(identifier)

        if not session:
            console.print(f"[red]{t('session_not_found', identifier=identifier)}[/]")
            return

        # Cannot delete current session
        if session.is_current:
            console.print(f"[yellow]{t('session_cannot_delete_current')}[/]")
            return

        msg_count = self.storage.get_session_message_count(session.id)
        if Confirm.ask(f"[yellow]{t('session_delete_confirm', name=session.name, count=msg_count)}[/]", default=False):
            self.storage.delete_session(session.id)
            console.print(f"[green]{SYM_CHECK()}[/] {t('session_deleted', name=session.name)}")

    def rename_current_session(self, new_name: str):
        """Rename the current session"""
        current_session = self.storage.get_current_session()
        if not current_session:
            console.print(f"[red]{t('session_no_current')}[/]")
            return

        self.storage.rename_session(current_session.id, new_name)
        console.print(f"[green]{SYM_CHECK()}[/] {t('session_renamed', name=new_name)}")
