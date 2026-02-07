"""
Connection Management Commands Mixin

Provides methods for managing database connections:
show, add, switch, edit, delete, test.
"""
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich import box

from db_agent.cli.ui import console, SYM_CHECK, SYM_CROSS
from db_agent.i18n import t
from db_agent.core.database import DatabaseToolsFactory
from db_agent.storage import DatabaseConnection, encrypt, decrypt


class ConnectionCommandsMixin:
    """Mixin for database connection management commands.

    Expects the host class to provide:
        self.storage   - SQLiteStorage instance
        self.agent     - SQLTuningAgent instance
    """

    def show_connections(self):
        """Show database connection list with action menu"""
        console.print()
        connections = self.storage.list_connections()

        if not connections:
            console.print(f"[dim]{t('connections_empty')}[/]")
            console.print()
            # No connections - jump straight into add wizard
            self.add_connection_wizard()
            return

        table = Table(box=box.ROUNDED, padding=(0, 2))
        table.add_column("#", style="cyan", justify="center", width=3)
        table.add_column(t("connection_name"), style="white")
        table.add_column(t("connection_type"), style="white")
        table.add_column(t("connection_host"), style="white")
        table.add_column(t("connection_database"), style="white")
        table.add_column(t("connection_status"), style="white")

        for i, conn in enumerate(connections, 1):
            status = f"[green]{t('connection_active')}[/]" if conn.is_active else ""
            table.add_row(
                str(i),
                conn.name,
                conn.db_type,
                f"{conn.host}:{conn.port}",
                conn.database,
                status
            )

        console.print(Panel(
            table,
            title=f"[bold cyan]{t('connections_title')}[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        # Action menu
        console.print()
        actions = [
            ("use", t("conn_action_use")),
            ("add", t("conn_action_add")),
            ("edit", t("conn_action_edit")),
            ("delete", t("conn_action_delete")),
            ("test", t("conn_action_test")),
        ]
        for i, (key, label) in enumerate(actions, 1):
            console.print(f"  [yellow]{i}.[/] {label}")
        console.print()

        choice = Prompt.ask(
            f"[cyan]{t('conn_select_action')}[/]",
            default=""
        )

        if not choice:
            return

        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(actions):
                console.print(f"[red]{t('invalid_choice')}[/]")
                return
        except ValueError:
            console.print(f"[red]{t('enter_valid_number')}[/]")
            return

        action_key = actions[idx][0]

        if action_key == "add":
            self.add_connection_wizard()
        elif action_key in ("use", "edit", "delete", "test"):
            selected = self._select_connection(connections)
            if not selected:
                return
            if action_key == "use":
                self.switch_connection(selected.name)
            elif action_key == "edit":
                self.edit_connection(selected.name)
            elif action_key == "delete":
                self.delete_connection(selected.name)
            elif action_key == "test":
                self.test_connection(selected.name)

    def _select_connection(self, connections=None):
        """Let user select a connection by number, return connection object or None"""
        if connections is None:
            connections = self.storage.list_connections()

        if not connections:
            console.print(f"[dim]{t('connections_empty')}[/]")
            return None

        console.print()
        for i, conn in enumerate(connections, 1):
            status = f" [green]({t('connection_active')})[/]" if conn.is_active else ""
            console.print(f"  [cyan]{i}.[/] {conn.name} ({conn.db_type} - {conn.host}:{conn.port}/{conn.database}){status}")
        console.print()

        choice = Prompt.ask(
            f"[cyan]{t('conn_select_target')}[/]",
            default=""
        )

        if not choice:
            console.print(f"[dim]{t('cancelled')}[/]")
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(connections):
                return connections[idx]
            else:
                console.print(f"[red]{t('invalid_choice')}[/]")
                return None
        except ValueError:
            console.print(f"[red]{t('enter_valid_number')}[/]")
            return None

    def handle_connection_command(self, args: str):
        """Handle /connection sub-commands"""
        parts = args.strip().split(maxsplit=1)
        if not parts:
            self.show_connections()
            return

        subcommand = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if subcommand == "add":
            self.add_connection_wizard()
        elif subcommand == "use":
            if arg:
                self.switch_connection(arg)
            else:
                selected = self._select_connection()
                if selected:
                    self.switch_connection(selected.name)
        elif subcommand == "edit":
            if arg:
                self.edit_connection(arg)
            else:
                selected = self._select_connection()
                if selected:
                    self.edit_connection(selected.name)
        elif subcommand == "delete":
            if arg:
                self.delete_connection(arg)
            else:
                selected = self._select_connection()
                if selected:
                    self.delete_connection(selected.name)
        elif subcommand == "use-db":
            self.list_and_switch_database()
        elif subcommand == "test":
            self.test_connection(arg)
        else:
            console.print(f"[red]{t('invalid_choice')}[/]")

    def add_connection_wizard(self):
        """Wizard for adding a new database connection"""
        console.print()
        console.print(f"[bold cyan]{t('setup_step_db')}[/]")
        console.print()

        # Select database type
        db_types = DatabaseToolsFactory.get_supported_types()
        for i, db_type in enumerate(db_types, 1):
            console.print(f"  [white]{i}.[/] {db_type}")

        console.print()
        choice = Prompt.ask(f"[cyan]{t('setup_db_type')}[/]", default="1")

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(db_types):
                db_type = db_types[idx]
            else:
                console.print(f"[red]{t('invalid_choice')}[/]")
                return
        except ValueError:
            console.print(f"[red]{t('enter_valid_number')}[/]")
            return

        # Default ports
        default_ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'gaussdb': 5432,
            'oracle': 1521,
            'sqlserver': 1433
        }

        # Collect connection details
        console.print()
        host = Prompt.ask(f"[cyan]{t('setup_db_host')}[/]", default="localhost")
        port_str = Prompt.ask(f"[cyan]{t('setup_db_port')}[/]", default=str(default_ports.get(db_type, 5432)))
        try:
            port = int(port_str)
        except ValueError:
            port = default_ports.get(db_type, 5432)

        database = Prompt.ask(f"[cyan]{t('setup_db_name')}[/]", default="postgres" if db_type in ['postgresql', 'gaussdb'] else "")
        username = Prompt.ask(f"[cyan]{t('setup_db_user')}[/]", default="postgres" if db_type in ['postgresql', 'gaussdb'] else "")
        password = Prompt.ask(f"[cyan]{t('setup_db_password')}[/]", password=True)

        # Generate default connection name
        default_name = f"{db_type}_{host}_{database}"
        conn_name = Prompt.ask(f"[cyan]{t('setup_conn_name')}[/]", default=default_name)

        # Test connection
        console.print()
        with console.status(f"[dim]{t('setup_testing_connection')}[/]", spinner="dots"):
            try:
                db_config = {
                    'type': db_type,
                    'host': host,
                    'port': port,
                    'database': database,
                    'user': username,
                    'password': password
                }
                test_tools = DatabaseToolsFactory.create(db_type, db_config)
                test_tools.get_db_info()  # Test connection
                console.print(f"[green]{SYM_CHECK()}[/] {t('setup_connection_success')}")
            except Exception as e:
                console.print(f"[red]{SYM_CROSS()}[/] {t('setup_connection_failed', error=str(e))}")
                if not Confirm.ask(f"[yellow]{t('setup_retry_connection')}[/]", default=True):
                    return
                self.add_connection_wizard()
                return

        # Save connection
        from datetime import datetime
        now = datetime.now()
        conn = DatabaseConnection(
            id=None,
            name=conn_name,
            db_type=db_type,
            host=host,
            port=port,
            database=database,
            username=username,
            password_encrypted=encrypt(password),
            is_active=False,
            created_at=now,
            updated_at=now
        )

        try:
            self.storage.add_connection(conn)
            console.print(f"[green]{SYM_CHECK()}[/] {t('connection_add_success', name=conn_name)}")

            # Ask if set as active
            if Confirm.ask(f"[cyan]{t('connection_switch_success', name=conn_name).replace(t('connection_switch_success', name=conn_name).split()[0], 'Set as active?')}[/]", default=True):
                self.storage.set_active_connection(conn_name)
        except Exception as e:
            console.print(f"[red]{t('error')}:[/] {e}")

        console.print()

    def switch_connection(self, name: str):
        """Switch active connection"""
        conn = self.storage.get_connection(name)
        if not conn:
            console.print(f"[red]{t('connection_not_found', name=name)}[/]")
            return

        self.storage.set_active_connection(name)
        console.print(f"[green]{SYM_CHECK()}[/] {t('connection_switch_success', name=name)}")

        # Reinitialize agent with new connection
        try:
            password = decrypt(conn.password_encrypted)
            db_config = {
                'type': conn.db_type,
                'host': conn.host,
                'port': conn.port,
                'database': conn.database,
                'user': conn.username,
                'password': password
            }
            self.agent.reinitialize_db_tools(db_config)
            console.print(f"[green]{SYM_CHECK()}[/] {t('connected')}")
        except Exception as e:
            console.print(f"[red]{SYM_CROSS()}[/] {t('connection_failed')}: {e}")

    def edit_connection(self, name: str):
        """Edit a connection"""
        conn = self.storage.get_connection(name)
        if not conn:
            console.print(f"[red]{t('connection_not_found', name=name)}[/]")
            return

        console.print()
        console.print(f"[cyan]Editing connection: {name}[/]")
        console.print(f"[dim]({t('input_press_enter_default')})[/]")
        console.print()

        host = Prompt.ask(f"[cyan]{t('setup_db_host')}[/]", default=conn.host)
        port = Prompt.ask(f"[cyan]{t('setup_db_port')}[/]", default=str(conn.port))
        database = Prompt.ask(f"[cyan]{t('setup_db_name')}[/]", default=conn.database)
        username = Prompt.ask(f"[cyan]{t('setup_db_user')}[/]", default=conn.username)
        password = Prompt.ask(f"[cyan]{t('setup_db_password')} (leave empty to keep)[/]", password=True, default="")

        conn.host = host
        conn.port = int(port)
        conn.database = database
        conn.username = username
        if password:
            conn.password_encrypted = encrypt(password)

        self.storage.update_connection(conn)
        console.print(f"[green]{SYM_CHECK()}[/] {t('connection_update_success', name=name)}")

    def delete_connection(self, name: str):
        """Delete a connection"""
        conn = self.storage.get_connection(name)
        if not conn:
            console.print(f"[red]{t('connection_not_found', name=name)}[/]")
            return

        if conn.is_active:
            console.print(f"[yellow]Warning: This is the active connection[/]")

        if Confirm.ask(f"[yellow]{t('connection_delete_confirm', name=name)}[/]", default=False):
            self.storage.delete_connection(name)
            console.print(f"[green]{SYM_CHECK()}[/] {t('connection_delete_success', name=name)}")

    def list_and_switch_database(self):
        """List databases on the current instance and switch to one"""
        active_conn = self.storage.get_active_connection()
        if not active_conn:
            console.print(f"[red]{t('connection_no_active')}[/]")
            return

        # Get database tools for the active connection
        password = decrypt(active_conn.password_encrypted)
        db_config = {
            'type': active_conn.db_type,
            'host': active_conn.host,
            'port': active_conn.port,
            'database': active_conn.database,
            'user': active_conn.username,
            'password': password
        }

        with console.status(f"[dim]{t('loading')}[/]", spinner="dots"):
            try:
                db_tools = DatabaseToolsFactory.create(active_conn.db_type, db_config)
                result = db_tools.list_databases()
            except Exception as e:
                console.print(f"[red]{t('error')}:[/] {e}")
                return

        if result.get("status") == "error":
            console.print(f"[red]{t('error')}:[/] {result.get('error')}")
            return

        databases = result.get("databases", [])
        if not databases:
            console.print(f"[dim]{t('connections_empty')}[/]")
            return

        # Display databases
        console.print()
        console.print(f"[bold cyan]{t('connection_list_databases')}[/] ({result.get('instance', '')})")
        console.print()
        for i, db in enumerate(databases, 1):
            current = " [green]◀ current[/]" if db.get("is_current") else ""
            size = f" [dim]({db.get('size', '')})[/]" if db.get("size") else ""
            console.print(f"  [cyan]{i}.[/] {db['name']}{size}{current}")
        console.print()

        choice = Prompt.ask(
            f"[cyan]{t('connection_use_db_prompt')}[/]",
            default=""
        )

        if not choice:
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(databases):
                target_db = databases[idx]["name"]
            else:
                console.print(f"[red]{t('invalid_choice')}[/]")
                return
        except ValueError:
            # Treat as database name
            target_db = choice.strip()

        if target_db == active_conn.database:
            console.print(f"[dim]{t('connection_current_database')}: {target_db}[/]")
            return

        self._switch_database(active_conn, target_db, password)

    def _switch_database(self, active_conn, target_database: str, password: str):
        """Switch to a different database on the same instance"""
        # Check if connection already exists
        found = self.storage.find_connection_for_instance_db(
            active_conn.db_type, active_conn.host, active_conn.port,
            active_conn.username, target_database
        )

        if found:
            self.storage.set_active_connection(found.name)
            console.print(f"[green]{SYM_CHECK()}[/] {t('connection_use_db_success', database=target_database, name=found.name)}")
        else:
            # Auto-create new connection
            new_name = f"{active_conn.name}__{target_database}"
            from datetime import datetime
            now = datetime.now()
            new_conn = DatabaseConnection(
                id=None,
                name=new_name,
                db_type=active_conn.db_type,
                host=active_conn.host,
                port=active_conn.port,
                database=target_database,
                username=active_conn.username,
                password_encrypted=active_conn.password_encrypted,
                is_active=False,
                created_at=now,
                updated_at=now
            )
            try:
                self.storage.add_connection(new_conn)
                self.storage.set_active_connection(new_name)
                console.print(f"[green]{SYM_CHECK()}[/] {t('connection_use_db_created', database=target_database, name=new_name)}")
            except Exception as e:
                console.print(f"[red]{t('error')}:[/] {e}")
                return

        # Reinitialize agent with new connection
        try:
            db_config = {
                'type': active_conn.db_type,
                'host': active_conn.host,
                'port': active_conn.port,
                'database': target_database,
                'user': active_conn.username,
                'password': password
            }
            self.agent.reinitialize_db_tools(db_config)
            console.print(f"[green]{SYM_CHECK()}[/] {t('connected')}")
        except Exception as e:
            console.print(f"[red]{SYM_CROSS()}[/] {t('connection_failed')}: {e}")

    def test_connection(self, name: str = None):
        """Test a connection"""
        if name:
            conn = self.storage.get_connection(name)
            if not conn:
                console.print(f"[red]{t('connection_not_found', name=name)}[/]")
                return
        else:
            conn = self.storage.get_active_connection()
            if not conn:
                console.print(f"[red]{t('connections_empty')}[/]")
                return
            name = conn.name

        with console.status(f"[dim]{t('setup_testing_connection')}[/]", spinner="dots"):
            try:
                password = decrypt(conn.password_encrypted)
                db_config = {
                    'type': conn.db_type,
                    'host': conn.host,
                    'port': conn.port,
                    'database': conn.database,
                    'user': conn.username,
                    'password': password
                }
                test_tools = DatabaseToolsFactory.create(conn.db_type, db_config)
                info = test_tools.get_db_info()
                console.print(f"[green]{SYM_CHECK()}[/] {t('connection_test_success', name=name)}")
                console.print(f"[dim]  {info.get('type', '')} {info.get('version', '')}[/]")
            except Exception as e:
                console.print(f"[red]{SYM_CROSS()}[/] {t('connection_test_failed', name=name, error=str(e))}")
