"""
Migration Commands Mixin

Provides methods for database migration wizards:
file-based migration and online migration.
"""
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich import box

from db_agent.cli.ui import console, SYM_CHECK
from db_agent.i18n import t


class MigrationCommandsMixin:
    """Mixin for database migration commands.

    Expects the host class to provide:
        self.storage    - SQLiteStorage instance
        self.agent      - SQLTuningAgent instance
        self.load_file() - Method to load SQL files
    """

    def migrate_wizard(self) -> str:
        """
        Database migration wizard (file-based).

        Returns:
            Generated migration instruction message, or None if cancelled.
        """
        console.print()

        # Get current connection's database type
        db_info = self.agent.db_tools.get_db_info()
        target_db = db_info.get("type", "postgresql")
        target_db_display = {
            "postgresql": "PostgreSQL",
            "mysql": "MySQL",
            "gaussdb": "GaussDB",
            "oracle": "Oracle"
        }.get(target_db, target_db.upper())

        console.print(f"[cyan]{t('migrate_target_db')}:[/] [green]{target_db_display}[/]")
        console.print()

        # Source database selection
        source_dbs = [
            ("oracle", "Oracle"),
            ("mysql", "MySQL"),
            ("postgresql", "PostgreSQL"),
            ("sqlserver", "SQL Server"),
            ("db2", "IBM DB2"),
            ("other", t("migrate_other"))
        ]

        # Filter out current database
        source_dbs = [(k, v) for k, v in source_dbs if k != target_db]

        table = Table(box=box.ROUNDED, padding=(0, 2))
        table.add_column("#", style="cyan", justify="center", width=3)
        table.add_column(t("migrate_source_db"), style="white")

        for i, (key, name) in enumerate(source_dbs, 1):
            table.add_row(str(i), name)

        console.print(Panel(
            table,
            title=f"[bold cyan]{t('migrate_select_source')}[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        console.print()
        choice = Prompt.ask(
            f"[cyan]{t('migrate_enter_number')}[/]",
            default=""
        )

        if not choice:
            console.print(f"[dim]{t('cancelled')}[/]")
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(source_dbs):
                source_db_key, source_db_name = source_dbs[idx]
            else:
                console.print(f"[red]{t('invalid_choice')}[/]")
                return None
        except ValueError:
            console.print(f"[red]{t('enter_valid_number')}[/]")
            return None

        # If "other" selected, prompt for name
        if source_db_key == "other":
            source_db_name = Prompt.ask(
                f"[cyan]{t('migrate_enter_source_name')}[/]",
                default=""
            )
            if not source_db_name:
                console.print(f"[dim]{t('cancelled')}[/]")
                return None

        console.print()
        console.print(f"[green]{SYM_CHECK()}[/] {t('migrate_source_selected', source=source_db_name)}")
        console.print()

        # Load SQL file
        file_path = Prompt.ask(
            f"[cyan]{t('file_input_path')}[/]",
            default=""
        )

        if not file_path:
            console.print(f"[dim]{t('cancelled')}[/]")
            return None

        # Use load_file method to load
        if not self.load_file(file_path):
            return None

        # Select migration mode
        console.print()
        console.print(f"[cyan]{t('migrate_mode_select')}:[/]")
        console.print(f"  [white]1.[/] {t('migrate_mode_convert_only')}")
        console.print(f"  [white]2.[/] {t('migrate_mode_convert_execute')}")
        console.print()

        mode_choice = Prompt.ask(
            f"[cyan]{t('migrate_enter_mode')}[/]",
            default="1"
        )

        if mode_choice == "2":
            execute_mode = True
            mode_text = t("migrate_will_execute")
        else:
            execute_mode = False
            mode_text = t("migrate_convert_only")

        console.print(f"[green]{SYM_CHECK()}[/] {mode_text}")
        console.print()

        # Build migration instruction - use specialized instructions for Oracle to GaussDB
        is_oracle_to_gaussdb = (source_db_key == "oracle" and target_db in ["gaussdb"])

        if is_oracle_to_gaussdb:
            # Use optimized Oracle->GaussDB migration instructions
            if execute_mode:
                migrate_instruction = t("migrate_instruction_oracle_to_gaussdb_execute")
            else:
                migrate_instruction = t("migrate_instruction_oracle_to_gaussdb_convert")
            console.print(f"[cyan]{t('migrate_using_optimized_rules')}[/]")
        else:
            # Use generic migration instructions
            if execute_mode:
                migrate_instruction = t("migrate_instruction_execute",
                                       source=source_db_name,
                                       target=target_db_display)
            else:
                migrate_instruction = t("migrate_instruction_convert",
                                       source=source_db_name,
                                       target=target_db_display)

        return migrate_instruction

    def migrate_online_wizard(self) -> str:
        """
        Online database object migration wizard.

        Returns:
            Generated migration instruction message, or None if cancelled.
        """
        console.print()
        console.print(Panel(
            f"[bold cyan]{t('migrate_online_title')}[/]",
            border_style="cyan"
        ))
        console.print()

        # Get current active connection (target)
        active_conn = self.storage.get_active_connection()
        if not active_conn:
            console.print(f"[red]{t('migrate_no_active_connection')}[/]")
            return None

        target_db_display = {
            "postgresql": "PostgreSQL",
            "mysql": "MySQL",
            "gaussdb": "GaussDB",
            "oracle": "Oracle",
            "sqlserver": "SQL Server"
        }.get(active_conn.db_type, active_conn.db_type.upper())

        console.print(f"[cyan]{t('migrate_target_db')}:[/] [green]{active_conn.name}[/] ({target_db_display})")
        console.print()

        # Get all connections (exclude current active connection)
        all_connections = self.storage.list_connections()
        source_connections = [c for c in all_connections if c.id != active_conn.id]

        if not source_connections:
            console.print(f"[yellow]{t('migrate_no_source_connections')}[/]")
            console.print(f"[dim]{t('migrate_add_source_hint')}[/]")
            return None

        # Show available source databases
        table = Table(box=box.ROUNDED, padding=(0, 2))
        table.add_column("#", style="cyan", justify="center", width=3)
        table.add_column(t("connection_name"), style="white")
        table.add_column(t("connection_type"), style="dim")
        table.add_column(t("connection_host"), style="dim")
        table.add_column(t("connection_database"), style="dim")

        for i, conn in enumerate(source_connections, 1):
            db_type_display = {
                "postgresql": "PostgreSQL",
                "mysql": "MySQL",
                "gaussdb": "GaussDB",
                "oracle": "Oracle",
                "sqlserver": "SQL Server"
            }.get(conn.db_type, conn.db_type.upper())
            table.add_row(str(i), conn.name, db_type_display, conn.host, conn.database)

        console.print(Panel(
            table,
            title=f"[bold cyan]{t('migrate_select_source_connection')}[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        console.print()
        choice = Prompt.ask(
            f"[cyan]{t('migrate_enter_number')}[/]",
            default=""
        )

        if not choice:
            console.print(f"[dim]{t('cancelled')}[/]")
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(source_connections):
                source_conn = source_connections[idx]
            else:
                console.print(f"[red]{t('invalid_choice')}[/]")
                return None
        except ValueError:
            console.print(f"[red]{t('enter_valid_number')}[/]")
            return None

        source_db_display = {
            "postgresql": "PostgreSQL",
            "mysql": "MySQL",
            "gaussdb": "GaussDB",
            "oracle": "Oracle",
            "sqlserver": "SQL Server"
        }.get(source_conn.db_type, source_conn.db_type.upper())

        console.print()
        console.print(f"[green]{SYM_CHECK()}[/] {t('migrate_source_selected', source=source_conn.name)} ({source_db_display})")
        console.print()

        # Confirm migration direction
        console.print(f"[cyan]{t('migrate_direction')}:[/]")
        console.print(f"  {source_conn.name} ({source_db_display}) -> {active_conn.name} ({target_db_display})")
        console.print()

        confirm = Prompt.ask(
            f"[cyan]{t('migrate_confirm_direction')}[/]",
            choices=["y", "n"],
            default="y"
        )

        if confirm.lower() != "y":
            console.print(f"[dim]{t('cancelled')}[/]")
            return None

        # Optional: specify schema
        console.print()
        source_schema = Prompt.ask(
            f"[cyan]{t('migrate_source_schema')}[/]",
            default=""
        )

        # Select SQL execution confirmation mode
        console.print()
        console.print(f"[cyan]{t('migrate_confirm_mode')}:[/]")
        console.print(f"  [green]1.[/] {t('migrate_confirm_mode_auto')}")
        console.print(f"  [yellow]2.[/] {t('migrate_confirm_mode_manual')}")
        console.print()
        mode_choice = Prompt.ask(
            f"[cyan]{t('migrate_enter_number')}[/]",
            choices=["1", "2"],
            default="1"
        )
        auto_execute = (mode_choice == "1")

        # Create migration task
        from datetime import datetime
        task_name = f"Migration_{source_conn.name}_to_{active_conn.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        import json as _json
        from db_agent.storage.models import MigrationTask
        task = MigrationTask(
            id=None,
            name=task_name,
            source_connection_id=source_conn.id,
            target_connection_id=active_conn.id,
            source_db_type=source_conn.db_type,
            target_db_type=active_conn.db_type,
            status="pending",
            total_items=0,
            completed_items=0,
            failed_items=0,
            skipped_items=0,
            source_schema=source_schema or None,
            target_schema=None,
            options=_json.dumps({"auto_execute": auto_execute}),
            analysis_result=None,
            error_message=None,
            started_at=None,
            completed_at=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        task_id = self.storage.create_migration_task(task)

        # Set Agent's migration auto-execute flag
        if auto_execute:
            self.agent.migration_auto_execute = True

        console.print()
        console.print(f"[green]{SYM_CHECK()}[/] {t('migrate_task_created', task_id=task_id, name=task_name)}")
        console.print()

        # Build migration instruction
        migrate_instruction = t(
            "migrate_online_instruction",
            task_id=task_id,
            source_name=source_conn.name,
            source_type=source_db_display,
            target_name=active_conn.name,
            target_type=target_db_display,
            source_schema=source_schema or "default"
        )

        return migrate_instruction
