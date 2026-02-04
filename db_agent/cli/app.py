"""
SQL Tuning AI Agent - Interactive CLI
交互式命令行界面
"""
import os
import sys
import logging

# 完全禁用日志输出
logging.disable(logging.CRITICAL)

# Windows console encoding fix
if sys.platform == 'win32':
    try:
        # Try to enable UTF-8 mode on Windows
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
    except Exception:
        pass

# Check if console supports Unicode
def _supports_unicode():
    """Check if the console supports Unicode output"""
    if sys.platform != 'win32':
        return True
    try:
        # Try to encode a Unicode character
        '✓'.encode(sys.stdout.encoding or 'utf-8')
        return True
    except (UnicodeEncodeError, LookupError):
        return False

_UNICODE_SUPPORT = _supports_unicode()

# Symbol mappings (Unicode -> ASCII fallback)
def sym(unicode_char: str, ascii_fallback: str = '') -> str:
    """Return Unicode symbol or ASCII fallback based on console support"""
    if _UNICODE_SUPPORT:
        return unicode_char
    return ascii_fallback

# Common symbols
SYM_CHECK = lambda: sym('✓', '+')
SYM_CROSS = lambda: sym('✗', 'x')
SYM_BULLET = lambda: sym('●', '*')

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.prompt import Confirm, Prompt
from rich import box

try:
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style
    from prompt_toolkit.history import FileHistory
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

import threading
import time

from db_agent.core import SQLTuningAgent
from db_agent.core.database import DatabaseToolsFactory
from db_agent.llm import LLMClientFactory
from db_agent.i18n import i18n, t
from db_agent.storage import SQLiteStorage, DatabaseConnection, LLMProvider, Session, ChatMessage, encrypt, decrypt
from .config import ConfigManager, migrate_from_ini, find_config_ini


class EscapeKeyListener:
    """ESC 键监听器（非阻塞）"""

    def __init__(self):
        self._listening = False
        self._thread = None
        self._callback = None
        self._old_settings = None

    def start(self, callback):
        """开始监听 ESC 键"""
        if self._listening:
            return

        self._callback = callback
        self._listening = True

        if sys.platform == 'win32':
            self._start_windows()
        else:
            self._start_unix()

    def _start_unix(self):
        """Unix/Mac 系统的 ESC 监听"""
        import tty
        import termios
        import select

        def listen():
            fd = sys.stdin.fileno()
            try:
                self._old_settings = termios.tcgetattr(fd)
                tty.setcbreak(fd)  # 使用 cbreak 模式，不需要回车

                while self._listening:
                    # 使用 select 进行非阻塞检测
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        ch = sys.stdin.read(1)
                        if ch == '\x1b':  # ESC
                            # 检查是否是ESC序列的开始（如方向键）
                            # 设置短暂超时来检测是否有后续字符
                            if select.select([sys.stdin], [], [], 0.05)[0]:
                                # 有后续字符，可能是方向键序列，跳过
                                sys.stdin.read(1)  # 读取 [
                                if select.select([sys.stdin], [], [], 0.05)[0]:
                                    sys.stdin.read(1)  # 读取方向键字符
                            else:
                                # 单独的 ESC 键
                                if self._callback:
                                    self._callback()
            except Exception:
                pass
            finally:
                if self._old_settings:
                    try:
                        termios.tcsetattr(fd, termios.TCSADRAIN, self._old_settings)
                    except Exception:
                        pass

        self._thread = threading.Thread(target=listen, daemon=True)
        self._thread.start()

    def _start_windows(self):
        """Windows 系统的 ESC 监听"""
        import msvcrt

        def listen():
            while self._listening:
                try:
                    if msvcrt.kbhit():
                        ch = msvcrt.getch()
                        if ch == b'\x1b':  # ESC
                            if self._callback:
                                self._callback()
                    else:
                        time.sleep(0.1)  # 防止CPU占用过高
                except Exception:
                    pass

        self._thread = threading.Thread(target=listen, daemon=True)
        self._thread.start()

    def stop(self):
        """停止监听"""
        self._listening = False

        # 恢复终端设置 (Unix)
        if sys.platform != 'win32' and self._old_settings:
            import termios
            try:
                fd = sys.stdin.fileno()
                termios.tcsetattr(fd, termios.TCSADRAIN, self._old_settings)
            except Exception:
                pass
            self._old_settings = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

        self._thread = None
        self._callback = None


console = Console()


def inline_select(title: str, options: list, default_index: int = 0) -> str:
    """
    内联交互式选择菜单（上下键选择，回车确认）

    Args:
        title: 菜单标题
        options: 选项列表 [(value, label), ...]
        default_index: 默认选中的索引

    Returns:
        选中的值
    """
    import sys
    import tty
    import termios

    def get_key():
        """读取单个按键"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # ESC sequence
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':
                        return 'up'
                    elif ch3 == 'B':
                        return 'down'
            elif ch == '\r' or ch == '\n':
                return 'enter'
            elif ch == 'q' or ch == '\x03':  # q or Ctrl+C
                return 'quit'
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def render(selected_idx):
        """渲染选项列表"""
        # 清除之前的选项显示
        sys.stdout.write(f"\033[{len(options)}A")  # 上移
        sys.stdout.write("\033[J")  # 清除到屏幕底部

        for i, (value, label) in enumerate(options):
            if i == selected_idx:
                sys.stdout.write(f"  \033[32m❯ {label}\033[0m\n")  # 绿色高亮
            else:
                sys.stdout.write(f"    {label}\n")
        sys.stdout.flush()

    # Windows 不支持 tty，使用 fallback
    if sys.platform == 'win32':
        return None

    try:
        current_idx = default_index

        # 初始渲染
        console.print(f"[yellow]{title}[/] [dim](↑↓选择, Enter确认)[/]")
        for i, (value, label) in enumerate(options):
            if i == current_idx:
                console.print(f"  [green]❯ {label}[/]")
            else:
                console.print(f"    {label}")

        while True:
            key = get_key()
            if key == 'up':
                current_idx = (current_idx - 1) % len(options)
                render(current_idx)
            elif key == 'down':
                current_idx = (current_idx + 1) % len(options)
                render(current_idx)
            elif key == 'enter':
                return options[current_idx][0]
            elif key == 'quit':
                return options[default_index][0]  # 返回默认值

    except Exception:
        return None


class AgentCLI:
    """AI Agent命令行界面"""

    def __init__(self, agent: SQLTuningAgent, storage: SQLiteStorage, config_manager: ConfigManager = None):
        self.agent = agent
        self.storage = storage
        self.config_manager = config_manager  # For backward compatibility
        self.current_session_id = None  # Track current session

        # 斜杠命令列表 (用于自动补全)
        self.slash_commands = [
            ("/help", "cmd_help"),
            ("/file", "cmd_file"),
            ("/migrate", "cmd_migrate"),
            ("/sessions", "cmd_sessions"),
            ("/session", "cmd_session"),
            ("/connections", "cmd_connections"),
            ("/providers", "cmd_providers"),
            ("/model", "cmd_model"),
            ("/language", "cmd_language"),
            ("/reset", "cmd_reset"),
            ("/history", "cmd_history"),
            ("/clear", "cmd_clear"),
            ("/exit", "cmd_exit"),
        ]

        self.commands = {
            "help": self.show_help,
            "/help": self.show_help,
            "model": self.show_model_menu,
            "/model": self.show_model_menu,
            "models": self.show_model_menu,
            "/sessions": self.show_sessions,
            "sessions": self.show_sessions,
            "/connections": self.show_connections,
            "connections": self.show_connections,
            "/providers": self.show_providers,
            "providers": self.show_providers,
            "language": self.show_language_menu,
            "/language": self.show_language_menu,
            "/lang": self.show_language_menu,
            "lang": self.show_language_menu,
            "reset": self.reset_conversation,
            "/reset": self.reset_conversation,
            "history": self.show_history,
            "/history": self.show_history,
            "clear": self.clear_screen,
            "/clear": self.clear_screen,
            "exit": self.exit_cli,
            "/exit": self.exit_cli,
            "quit": self.exit_cli,
            "/quit": self.exit_cli
        }

        # 当前加载的文件内容
        self._loaded_file_content = None
        self._loaded_file_path = None

        # 设置prompt_toolkit自动补全和命令历史
        if PROMPT_TOOLKIT_AVAILABLE:
            self.command_completer = WordCompleter(
                [cmd for cmd, _ in self.slash_commands],
                ignore_case=True,
                match_middle=False
            )
            self.pt_style = Style.from_dict({
                'completion-menu.completion': 'bg:#333333 #ffffff',
                'completion-menu.completion.current': 'bg:#00aaaa #000000',
                'scrollbar.background': 'bg:#333333',
                'scrollbar.button': 'bg:#666666',
            })
            # 命令历史文件
            history_dir = os.path.expanduser("~/.db_agent")
            os.makedirs(history_dir, exist_ok=True)
            history_file = os.path.join(history_dir, "command_history")
            self.command_history = FileHistory(history_file)
        else:
            self.command_history = None

        # ESC 键监听器
        self.esc_listener = EscapeKeyListener()
        self._was_interrupted = False

    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_command_menu(self) -> str:
        """显示命令菜单并返回选择的命令"""
        console.print()

        table = Table(box=box.ROUNDED, padding=(0, 2))
        table.add_column("#", style="cyan", justify="center", width=3)
        table.add_column("Command", style="green", width=12)
        table.add_column("Description", style="white")

        for i, (cmd, desc_key) in enumerate(self.slash_commands, 1):
            table.add_row(str(i), cmd, t(desc_key))

        console.print(Panel(
            table,
            title="[bold cyan]Commands[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        console.print()
        choice = Prompt.ask(
            "[cyan]Select command number (empty to cancel)[/]",
            default=""
        )

        if not choice:
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.slash_commands):
                return self.slash_commands[idx][0]
        except ValueError:
            pass

        return None

    def show_help(self):
        """显示帮助信息"""
        help_table = Table(box=box.ROUNDED, show_header=False, padding=(0, 2))
        help_table.add_column(t("help_title"), style="cyan bold")
        help_table.add_column("", style="white")

        help_table.add_row("/help", t("cmd_help"))
        help_table.add_row("/file [path]", t("cmd_file"))
        help_table.add_row("/migrate", t("cmd_migrate"))
        help_table.add_row("/sessions", t("cmd_sessions"))
        help_table.add_row("/session <new|use|delete|rename>", t("cmd_session"))
        help_table.add_row("/connections", t("cmd_connections"))
        help_table.add_row("/connection <add|use|edit|delete|test>", "Manage connections")
        help_table.add_row("/providers", t("cmd_providers"))
        help_table.add_row("/provider <add|use|edit|delete>", "Manage AI models")
        help_table.add_row("/model", t("cmd_model"))
        help_table.add_row("/language", t("cmd_language"))
        help_table.add_row("/reset", t("cmd_reset"))
        help_table.add_row("/history", t("cmd_history"))
        help_table.add_row("/clear", t("cmd_clear"))
        help_table.add_row("/exit", t("cmd_exit"))

        console.print()
        console.print(Panel(
            help_table,
            title=f"[bold cyan]{t('help_title')}[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        examples = Table(box=box.ROUNDED, show_header=False, padding=(0, 2))
        examples.add_column(t("examples_title"), style="green")

        examples.add_row(t("example_list_tables"))
        examples.add_row(t("example_describe_table"))
        examples.add_row(t("example_sample_data"))
        examples.add_row(t("example_create_table"))
        examples.add_row(t("example_insert"))
        examples.add_row(t("example_optimize"))

        console.print()
        console.print(Panel(
            examples,
            title=f"[bold green]{t('examples_title')}[/]",
            border_style="green",
            box=box.ROUNDED
        ))
        console.print()

    def show_model_menu(self):
        """显示模型切换菜单"""
        console.print()

        # 当前模型
        current = self.agent.get_current_model_info()
        console.print(f"[dim]{t('current_model')}:[/] [cyan]{current['provider']}[/] - [green]{current['model']}[/]")
        console.print()

        # 可用模型列表
        configured = self.config_manager.get_configured_providers()
        all_providers = LLMClientFactory.get_available_providers()

        table = Table(box=box.ROUNDED, padding=(0, 2))
        table.add_column("#", style="cyan", justify="center")
        table.add_column("Provider", style="white")
        table.add_column("Status", style="white")

        for i, (key, name) in enumerate(all_providers.items(), 1):
            if key in configured:
                status = f"[green]{t('model_configured')}[/]"
            else:
                status = f"[dim]{t('model_not_configured')}[/]"
            table.add_row(str(i), name, status)

        console.print(Panel(
            table,
            title=f"[bold cyan]{t('available_models')}[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        console.print()
        choice = Prompt.ask(
            f"[cyan]{t('select_model')}[/]",
            default=""
        )

        if not choice:
            console.print(f"[dim]{t('cancelled')}[/]")
            return

        try:
            idx = int(choice) - 1
            provider_keys = list(all_providers.keys())
            if 0 <= idx < len(provider_keys):
                provider = provider_keys[idx]
                self.switch_to_provider(provider)
            else:
                console.print(f"[red]{t('invalid_choice')}[/]")
        except ValueError:
            console.print(f"[red]{t('enter_valid_number')}[/]")

        console.print()

    def switch_to_provider(self, provider: str):
        """切换到指定提供商"""
        provider_config = self.config_manager.get_provider_config(provider)

        if not provider_config or not provider_config.get("api_key"):
            console.print(f"[red]{t('error')}:[/] {provider} {t('model_not_configured_error')}")
            console.print(f"[dim]{t('model_config_hint', provider=provider)}[/]")
            return

        try:
            client = LLMClientFactory.create(
                provider=provider,
                api_key=provider_config["api_key"],
                model=provider_config.get("model"),
                base_url=provider_config.get("base_url")
            )
            self.agent.switch_model(client)
            console.print(f"[green]{SYM_CHECK()}[/] {t('model_switched')} [cyan]{client.get_provider_name()}[/] - [green]{client.get_model_name()}[/]")
        except Exception as e:
            console.print(f"[red]{t('model_switch_failed')}:[/] {e}")

    def show_language_menu(self):
        """显示语言切换菜单"""
        console.print()

        languages = i18n.get_available_languages()
        current_lang = i18n.lang

        table = Table(box=box.ROUNDED, padding=(0, 2))
        table.add_column("#", style="cyan", justify="center")
        table.add_column(t("select_language"), style="white")
        table.add_column("", style="white")

        for i, (code, name) in enumerate(languages.items(), 1):
            marker = f"[green]{SYM_CHECK()}[/]" if code == current_lang else ""
            table.add_row(str(i), name, marker)

        console.print(Panel(
            table,
            title=f"[bold cyan]{t('select_language')}[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        console.print()
        choice = Prompt.ask(
            f"[cyan]{t('select_model')}[/]",
            default=""
        )

        if not choice:
            console.print(f"[dim]{t('cancelled')}[/]")
            return

        try:
            idx = int(choice) - 1
            lang_keys = list(languages.keys())
            if 0 <= idx < len(lang_keys):
                new_lang = lang_keys[idx]
                i18n.lang = new_lang
                # 更新Agent的语言（更新system prompt）
                self.agent.set_language(new_lang)
                # 保存语言设置
                if self.storage:
                    self.storage.set_preference('language', new_lang)
                elif self.config_manager:
                    self.config_manager.set_language(new_lang)
                console.print(f"[green]{SYM_CHECK()}[/] {t('language_switched')}")
            else:
                console.print(f"[red]{t('invalid_choice')}[/]")
        except ValueError:
            console.print(f"[red]{t('enter_valid_number')}[/]")

        console.print()

    # ==================== Connection Management ====================

    def show_connections(self):
        """显示数据库连接列表"""
        console.print()
        connections = self.storage.list_connections()

        if not connections:
            console.print(f"[dim]{t('connections_empty')}[/]")
            console.print()
            console.print(f"[cyan]{t('input_hint', help='/connection add', model='', lang='', exit='')}[/]")
            console.print()
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

        # Show sub-commands
        console.print()
        console.print("[dim]Commands: /connection add | /connection use <name> | /connection edit <name> | /connection delete <name> | /connection test [name][/]")
        console.print()

    def handle_connection_command(self, args: str):
        """处理 /connection 子命令"""
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
                console.print(f"[red]{t('error')}:[/] /connection use <name>")
        elif subcommand == "edit":
            if arg:
                self.edit_connection(arg)
            else:
                console.print(f"[red]{t('error')}:[/] /connection edit <name>")
        elif subcommand == "delete":
            if arg:
                self.delete_connection(arg)
            else:
                console.print(f"[red]{t('error')}:[/] /connection delete <name>")
        elif subcommand == "test":
            self.test_connection(arg)
        else:
            console.print(f"[red]{t('invalid_choice')}[/]")

    def add_connection_wizard(self):
        """添加新数据库连接的向导"""
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
        """切换活跃连接"""
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
        """编辑连接"""
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
        """删除连接"""
        conn = self.storage.get_connection(name)
        if not conn:
            console.print(f"[red]{t('connection_not_found', name=name)}[/]")
            return

        if conn.is_active:
            console.print(f"[yellow]Warning: This is the active connection[/]")

        if Confirm.ask(f"[yellow]{t('connection_delete_confirm', name=name)}[/]", default=False):
            self.storage.delete_connection(name)
            console.print(f"[green]{SYM_CHECK()}[/] {t('connection_delete_success', name=name)}")

    def test_connection(self, name: str = None):
        """测试连接"""
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

    # ==================== Provider Management ====================

    def show_providers(self):
        """显示 LLM 提供者列表"""
        console.print()
        providers = self.storage.list_providers()

        if not providers:
            console.print(f"[dim]{t('providers_empty')}[/]")
            console.print()
            console.print(f"[cyan]{t('input_hint', help='/provider add', model='', lang='', exit='')}[/]")
            console.print()
            return

        table = Table(box=box.ROUNDED, padding=(0, 2))
        table.add_column("#", style="cyan", justify="center", width=3)
        table.add_column(t("provider_name"), style="white")
        table.add_column(t("provider_type"), style="white")
        table.add_column(t("provider_model"), style="white")
        table.add_column(t("provider_status"), style="white")

        for i, provider in enumerate(providers, 1):
            status = f"[green]{t('provider_default')}[/]" if provider.is_default else ""
            table.add_row(
                str(i),
                provider.name,
                provider.provider,
                provider.model,
                status
            )

        console.print(Panel(
            table,
            title=f"[bold cyan]{t('providers_title')}[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        # Show sub-commands
        console.print()
        console.print("[dim]Commands: /provider add | /provider use <name> | /provider edit <name> | /provider delete <name>[/]")
        console.print()

    def handle_provider_command(self, args: str):
        """处理 /provider 子命令"""
        parts = args.strip().split(maxsplit=1)
        if not parts:
            self.show_providers()
            return

        subcommand = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if subcommand == "add":
            self.add_provider_wizard()
        elif subcommand == "use":
            if arg:
                self.switch_provider(arg)
            else:
                console.print(f"[red]{t('error')}:[/] /provider use <name>")
        elif subcommand == "edit":
            if arg:
                self.edit_provider(arg)
            else:
                console.print(f"[red]{t('error')}:[/] /provider edit <name>")
        elif subcommand == "delete":
            if arg:
                self.delete_provider(arg)
            else:
                console.print(f"[red]{t('error')}:[/] /provider delete <name>")
        else:
            console.print(f"[red]{t('invalid_choice')}[/]")

    def add_provider_wizard(self):
        """添加新 LLM 提供者的向导"""
        console.print()
        console.print(f"[bold cyan]{t('setup_step_llm')}[/]")
        console.print()

        # Select provider type
        providers = LLMClientFactory.get_available_providers()
        provider_keys = list(providers.keys())

        for i, (key, name) in enumerate(providers.items(), 1):
            recommended = t('setup_provider_recommended') if key == 'deepseek' else ''
            console.print(f"  [white]{i}.[/] {name} {recommended}")

        console.print()
        choice = Prompt.ask(f"[cyan]{t('setup_select_provider')}[/]", default="1")

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(provider_keys):
                provider_type = provider_keys[idx]
            else:
                console.print(f"[red]{t('invalid_choice')}[/]")
                return
        except ValueError:
            console.print(f"[red]{t('enter_valid_number')}[/]")
            return

        provider_info = LLMClientFactory.PROVIDERS[provider_type]
        default_model = provider_info['default_model']

        # Collect provider details
        console.print()
        api_key = Prompt.ask(f"[cyan]{t('setup_api_key_hint', provider=provider_info['name'])}[/]", password=True)
        model = Prompt.ask(f"[cyan]{t('setup_model')} ({t('setup_model_default', model=default_model)})[/]", default=default_model)

        base_url = None
        if provider_info.get('base_url'):
            base_url = Prompt.ask(f"[cyan]{t('setup_base_url')} ({t('setup_base_url_hint')})[/]", default=provider_info['base_url'])

        # Provider name (use provider type as default)
        provider_name = Prompt.ask(f"[cyan]{t('setup_provider_name')}[/]", default=provider_type)

        # Test API
        console.print()
        with console.status(f"[dim]{t('setup_testing_api')}[/]", spinner="dots"):
            try:
                test_client = LLMClientFactory.create(
                    provider=provider_type,
                    api_key=api_key,
                    model=model,
                    base_url=base_url
                )
                # Simple test - just verify client creation succeeded
                console.print(f"[green]{SYM_CHECK()}[/] {t('setup_api_success')}")
            except Exception as e:
                console.print(f"[red]{SYM_CROSS()}[/] {t('setup_api_failed', error=str(e))}")
                if not Confirm.ask(f"[yellow]{t('setup_retry_api')}[/]", default=True):
                    return
                self.add_provider_wizard()
                return

        # Save provider
        from datetime import datetime
        now = datetime.now()

        # Check if this is the first provider
        existing_providers = self.storage.list_providers()
        is_default = len(existing_providers) == 0

        provider = LLMProvider(
            id=None,
            name=provider_name,
            provider=provider_type,
            api_key_encrypted=encrypt(api_key),
            model=model,
            base_url=base_url,
            is_default=is_default,
            created_at=now,
            updated_at=now
        )

        try:
            self.storage.add_provider(provider)
            console.print(f"[green]{SYM_CHECK()}[/] {t('provider_add_success', name=provider_name)}")

            # Ask if set as default
            if not is_default:
                if Confirm.ask(f"[cyan]Set as default?[/]", default=False):
                    self.storage.set_default_provider(provider_name)
        except Exception as e:
            console.print(f"[red]{t('error')}:[/] {e}")

        console.print()

    def switch_provider(self, name: str):
        """切换默认提供者"""
        provider = self.storage.get_provider(name)
        if not provider:
            console.print(f"[red]{t('provider_not_found', name=name)}[/]")
            return

        self.storage.set_default_provider(name)
        console.print(f"[green]{SYM_CHECK()}[/] {t('provider_switch_success', name=name)}")

        # Switch agent's LLM client
        try:
            api_key = decrypt(provider.api_key_encrypted)
            client = LLMClientFactory.create(
                provider=provider.provider,
                api_key=api_key,
                model=provider.model,
                base_url=provider.base_url
            )
            self.agent.switch_model(client)
            console.print(f"[green]{SYM_CHECK()}[/] {t('model_switched')} [cyan]{client.get_provider_name()}[/] - [green]{client.get_model_name()}[/]")
        except Exception as e:
            console.print(f"[red]{SYM_CROSS()}[/] {t('model_switch_failed')}: {e}")

    def edit_provider(self, name: str):
        """编辑提供者"""
        provider = self.storage.get_provider(name)
        if not provider:
            console.print(f"[red]{t('provider_not_found', name=name)}[/]")
            return

        console.print()
        console.print(f"[cyan]Editing provider: {name}[/]")
        console.print(f"[dim]({t('input_press_enter_default')})[/]")
        console.print()

        model = Prompt.ask(f"[cyan]{t('setup_model')}[/]", default=provider.model)
        api_key = Prompt.ask(f"[cyan]{t('setup_api_key')} (leave empty to keep)[/]", password=True, default="")
        base_url = Prompt.ask(f"[cyan]{t('setup_base_url')}[/]", default=provider.base_url or "")

        provider.model = model
        if api_key:
            provider.api_key_encrypted = encrypt(api_key)
        if base_url:
            provider.base_url = base_url

        self.storage.update_provider(provider)
        console.print(f"[green]{SYM_CHECK()}[/] {t('provider_update_success', name=name)}")

    def delete_provider(self, name: str):
        """删除提供者"""
        provider = self.storage.get_provider(name)
        if not provider:
            console.print(f"[red]{t('provider_not_found', name=name)}[/]")
            return

        providers = self.storage.list_providers()
        if len(providers) <= 1:
            console.print(f"[red]{t('provider_cannot_delete_only')}[/]")
            return

        if provider.is_default:
            console.print(f"[yellow]{t('provider_cannot_delete_default')}[/]")
            return

        if Confirm.ask(f"[yellow]{t('provider_delete_confirm', name=name)}[/]", default=False):
            self.storage.delete_provider(name)
            console.print(f"[green]{SYM_CHECK()}[/] {t('provider_delete_success', name=name)}")

    # ==================== Session Management ====================

    def show_sessions(self):
        """显示会话列表"""
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
        """处理 /session 子命令"""
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
        """创建新会话"""
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
        """切换到指定会话"""
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

    def delete_session(self, identifier: str):
        """删除会话"""
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
        """重命名当前会话"""
        current_session = self.storage.get_current_session()
        if not current_session:
            console.print(f"[red]{t('session_no_current')}[/]")
            return

        self.storage.rename_session(current_session.id, new_name)
        console.print(f"[green]{SYM_CHECK()}[/] {t('session_renamed', name=new_name)}")

    def reset_conversation(self):
        """重置对话"""
        self.agent.reset_conversation()
        console.print()
        console.print(f"[green]{SYM_CHECK()}[/] {t('conversation_reset')}")
        console.print()

    def show_history(self):
        """显示对话历史"""
        history = self.agent.get_conversation_history()

        if not history:
            console.print()
            console.print(f"[dim]{t('no_history')}[/]")
            console.print()
            return

        console.print()
        for idx, message in enumerate(history, 1):
            role = message["role"]
            content = message["content"]

            if role == "user":
                if isinstance(content, str):
                    console.print(f"[cyan bold]You:[/] {content[:200]}{'...' if len(content) > 200 else ''}")
            elif role == "assistant":
                if isinstance(content, str):
                    console.print(f"[magenta bold]Agent:[/] {content[:200]}{'...' if len(content) > 200 else ''}")
            console.print()

    def load_file(self, file_path: str = None) -> bool:
        """
        加载SQL文件

        Args:
            file_path: 文件路径，如果为None则提示用户输入

        Returns:
            是否成功加载
        """
        console.print()

        # 如果没有提供路径，提示用户输入
        if not file_path:
            file_path = Prompt.ask(
                f"[cyan]{t('file_input_path')}[/]",
                default=""
            )

        if not file_path:
            console.print(f"[dim]{t('cancelled')}[/]")
            return False

        # 处理路径（支持引号包裹的路径）
        file_path = file_path.strip().strip('"').strip("'")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            console.print(f"[red]{t('error')}:[/] {t('file_not_found', path=file_path)}")
            return False

        # 检查文件扩展名
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.sql', '.txt', '']:
            console.print(f"[yellow]{t('file_type_warning', ext=ext)}[/]")

        # 读取文件
        try:
            # 尝试多种编码
            content = None
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                console.print(f"[red]{t('error')}:[/] {t('file_encoding_error')}")
                return False

            # 检查文件大小
            file_size = len(content)
            if file_size > 100000:  # 100KB
                console.print(f"[yellow]{t('file_size_warning', size=file_size // 1024)}[/]")
                if not Confirm.ask(f"[yellow]{t('file_continue_large')}[/]", default=False):
                    console.print(f"[dim]{t('cancelled')}[/]")
                    return False

            # 保存内容
            self._loaded_file_content = content
            self._loaded_file_path = file_path

            # 统计SQL语句数量
            sql_count = self._count_sql_statements(content)

            console.print(f"[green]{SYM_CHECK()}[/] {t('file_loaded', path=os.path.basename(file_path), size=file_size, sql_count=sql_count)}")
            console.print()

            # 显示文件预览
            preview_lines = content.split('\n')[:20]
            preview_text = '\n'.join(preview_lines)
            if len(preview_lines) < len(content.split('\n')):
                preview_text += f"\n... ({t('file_more_lines', count=len(content.split(chr(10))) - 20)})"

            console.print(Panel(
                Syntax(preview_text, "sql", theme="monokai", word_wrap=True, line_numbers=True),
                title=f"[bold cyan]{t('file_preview')} - {os.path.basename(file_path)}[/]",
                border_style="cyan",
                box=box.ROUNDED
            ))

            console.print()
            console.print(f"[dim]{t('file_usage_hint')}[/]")
            console.print()

            return True

        except Exception as e:
            console.print(f"[red]{t('error')}:[/] {t('file_read_error', error=str(e))}")
            return False

    def _count_sql_statements(self, content: str) -> int:
        """统计SQL语句数量（简单计算分号）"""
        # 移除注释
        lines = content.split('\n')
        clean_lines = []
        in_block_comment = False
        for line in lines:
            if '/*' in line:
                in_block_comment = True
            if '*/' in line:
                in_block_comment = False
                continue
            if in_block_comment:
                continue
            if line.strip().startswith('--'):
                continue
            clean_lines.append(line)

        clean_content = '\n'.join(clean_lines)
        # 计算分号数量
        return clean_content.count(';')

    def get_file_context(self) -> str:
        """获取当前加载的文件内容作为上下文"""
        if self._loaded_file_content:
            return f"\n\n---\n{t('file_context_header', path=self._loaded_file_path)}:\n```sql\n{self._loaded_file_content}\n```\n---\n"
        return ""

    def clear_loaded_file(self):
        """清除已加载的文件"""
        self._loaded_file_content = None
        self._loaded_file_path = None

    def migrate_wizard(self) -> str:
        """
        数据库迁移向导

        Returns:
            生成的迁移指令消息，如果取消则返回None
        """
        console.print()

        # 获取当前连接的数据库类型
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

        # 源数据库选择
        source_dbs = [
            ("oracle", "Oracle"),
            ("mysql", "MySQL"),
            ("postgresql", "PostgreSQL"),
            ("sqlserver", "SQL Server"),
            ("db2", "IBM DB2"),
            ("other", t("migrate_other"))
        ]

        # 过滤掉当前数据库
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

        # 如果选择"其他"，提示输入
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

        # 加载SQL文件
        file_path = Prompt.ask(
            f"[cyan]{t('file_input_path')}[/]",
            default=""
        )

        if not file_path:
            console.print(f"[dim]{t('cancelled')}[/]")
            return None

        # 使用load_file方法加载
        if not self.load_file(file_path):
            return None

        # 选择迁移模式
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

        # 构建迁移指令 - 针对Oracle到GaussDB使用专用指令
        is_oracle_to_gaussdb = (source_db_key == "oracle" and target_db in ["gaussdb"])

        if is_oracle_to_gaussdb:
            # 使用专门优化的Oracle→GaussDB迁移指令
            if execute_mode:
                migrate_instruction = t("migrate_instruction_oracle_to_gaussdb_execute")
            else:
                migrate_instruction = t("migrate_instruction_oracle_to_gaussdb_convert")
            console.print(f"[cyan]{t('migrate_using_optimized_rules')}[/]")
        else:
            # 使用通用迁移指令
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
        在线数据库对象迁移向导

        Returns:
            生成的迁移指令消息，如果取消则返回None
        """
        console.print()
        console.print(Panel(
            f"[bold cyan]{t('migrate_online_title')}[/]",
            border_style="cyan"
        ))
        console.print()

        # 获取当前活跃连接（目标库）
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

        # 获取所有连接（排除当前活跃连接）
        all_connections = self.storage.list_connections()
        source_connections = [c for c in all_connections if c.id != active_conn.id]

        if not source_connections:
            console.print(f"[yellow]{t('migrate_no_source_connections')}[/]")
            console.print(f"[dim]{t('migrate_add_source_hint')}[/]")
            return None

        # 显示可选的源数据库
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

        # 确认迁移方向
        console.print(f"[cyan]{t('migrate_direction')}:[/]")
        console.print(f"  {source_conn.name} ({source_db_display}) → {active_conn.name} ({target_db_display})")
        console.print()

        confirm = Prompt.ask(
            f"[cyan]{t('migrate_confirm_direction')}[/]",
            choices=["y", "n"],
            default="y"
        )

        if confirm.lower() != "y":
            console.print(f"[dim]{t('cancelled')}[/]")
            return None

        # 可选：指定schema
        console.print()
        source_schema = Prompt.ask(
            f"[cyan]{t('migrate_source_schema')}[/]",
            default=""
        )

        # 创建迁移任务
        from datetime import datetime
        task_name = f"Migration_{source_conn.name}_to_{active_conn.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

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
            options=None,
            analysis_result=None,
            error_message=None,
            started_at=None,
            completed_at=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        task_id = self.storage.create_migration_task(task)

        console.print()
        console.print(f"[green]{SYM_CHECK()}[/] {t('migrate_task_created', task_id=task_id, name=task_name)}")
        console.print()

        # 构建迁移指令
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

    def exit_cli(self):
        """退出CLI"""
        # 确保停止 ESC 监听
        self.esc_listener.stop()
        console.print()
        console.print(f"[dim]{t('goodbye')}[/]")
        console.print()
        sys.exit(0)

    def get_tool_label(self, tool_name: str) -> str:
        """获取工具的本地化名称"""
        tool_keys = {
            "list_tables": "tool_list_tables",
            "describe_table": "tool_describe_table",
            "get_sample_data": "tool_sample_data",
            "execute_sql": "tool_execute_sql",
            "execute_safe_query": "tool_safe_query",
            "run_explain": "tool_explain",
            "check_index_usage": "tool_check_index",
            "get_table_stats": "tool_table_stats",
            "create_index": "tool_create_index",
            "analyze_table": "tool_analyze",
            "identify_slow_queries": "tool_slow_queries",
            "get_running_queries": "tool_running_queries"
        }
        key = tool_keys.get(tool_name, tool_name)
        return t(key) if key != tool_name else tool_name

    def show_tool_call(self, tool_name: str, tool_input: dict):
        """显示工具调用"""
        label = self.get_tool_label(tool_name)

        param_text = ""
        if "sql" in tool_input:
            sql = tool_input["sql"]
            if len(sql) > 60:
                sql = sql[:60] + "..."
            param_text = f" [dim]{sql}[/]"
        elif "table_name" in tool_input:
            schema = tool_input.get("schema", "public")
            param_text = f" [dim]{schema}.{tool_input['table_name']}[/]"
        elif "index_sql" in tool_input:
            param_text = f" [dim]{tool_input['index_sql'][:50]}...[/]"

        console.print(f"  [yellow]{SYM_BULLET()}[/] {label}{param_text}")

    def show_tool_result(self, tool_name: str, result: dict):
        """显示工具结果"""
        status = result.get("status", "unknown")

        if status == "success":
            if "count" in result:
                console.print(f"    [green]{SYM_CHECK()}[/] [dim]{t('returned_records', count=result['count'])}[/]")
            elif "affected_rows" in result:
                console.print(f"    [green]{SYM_CHECK()}[/] [dim]{t('affected_rows', count=result['affected_rows'])}[/]")
            else:
                console.print(f"    [green]{SYM_CHECK()}[/] [dim]{t('success')}[/]")
        elif status == "pending_confirmation":
            console.print(f"    [yellow]⏳[/] [dim]{t('waiting_confirm')}[/]")
        elif status == "error":
            error = result.get('error', t('error'))
            if len(error) > 60:
                error = error[:60] + "..."
            console.print(f"    [red]{SYM_CROSS()}[/] [dim]{error}[/]")

    def run(self):
        """运行交互式CLI"""
        self.clear_screen()

        # 标题
        current = self.agent.get_current_model_info()
        title = Text()
        title.append(t("app_name"), style="bold magenta")
        title.append(" - ", style="dim")
        title.append(f"{current['provider']}", style="cyan")
        title.append(" / ", style="dim")
        title.append(f"{current['model']}", style="green")

        console.print()
        console.print(Panel(
            title,
            box=box.ROUNDED,
            border_style="magenta",
            padding=(0, 2)
        ))

        # 连接状态
        console.print()
        with console.status(f"[dim]{t('connecting')}[/]", spinner="dots"):
            try:
                # Use database info from the tools (already fetched during init)
                db_info = self.agent.db_tools.get_db_info()
                db_type = db_info.get("type", "postgresql").upper()
                version = db_info.get("version", "unknown")
                console.print(f"[green]{SYM_CHECK()}[/] {t('connected')}: [dim]{db_type} {version}[/]")
            except Exception as e:
                console.print(f"[red]{SYM_CROSS()}[/] {t('connection_failed')}: [dim]{e}[/]")

        console.print()
        console.print(f"[dim]{t('input_hint', help='/help', model='/model', lang='/language', exit='/exit')}[/]")
        if PROMPT_TOOLKIT_AVAILABLE:
            console.print(f"[dim]{t('autocomplete_hint')}[/]")
        console.print()

        # 主循环
        while True:
            try:
                # 显示当前模型的简短提示
                current = self.agent.get_current_model_info()
                prompt_prefix = f"{current['provider'][:2]}> "

                # 使用prompt_toolkit获取输入(支持自动补全)
                if PROMPT_TOOLKIT_AVAILABLE:
                    try:
                        user_input = pt_prompt(
                            prompt_prefix,
                            completer=self.command_completer,
                            style=self.pt_style,
                            history=self.command_history,
                            complete_while_typing=True
                        ).strip()
                    except (EOFError, KeyboardInterrupt):
                        raise KeyboardInterrupt
                else:
                    user_input = Prompt.ask(f"[bold cyan]{prompt_prefix}[/]").strip()

                if not user_input:
                    continue

                # 处理单独的 "/" 输入 - 显示命令菜单
                if user_input == "/":
                    selected_cmd = self.show_command_menu()
                    if selected_cmd and selected_cmd.lower() in self.commands:
                        self.commands[selected_cmd.lower()]()
                    continue

                # 检查特殊命令
                if user_input.lower() in self.commands:
                    self.commands[user_input.lower()]()
                    continue

                # 处理 /file 命令 (带参数)
                if user_input.lower().startswith('/file'):
                    parts = user_input.split(maxsplit=1)
                    file_path = parts[1].strip() if len(parts) > 1 else None
                    self.load_file(file_path)
                    continue

                # 处理 /migrate 命令 - 数据库迁移向导
                if user_input.lower().startswith('/migrate'):
                    parts = user_input.lower().split(maxsplit=1)
                    sub_cmd = parts[1].strip() if len(parts) > 1 else ""

                    # 如果没有子命令，显示选择菜单
                    if not sub_cmd:
                        console.print(f"\n[bold cyan]{t('cmd_migrate')}[/]")
                        console.print(f"  [yellow]1.[/] {t('migrate_mode_file')} - {t('migrate_mode_file_desc')}")
                        console.print(f"  [yellow]2.[/] {t('migrate_mode_online')} - {t('migrate_mode_online_desc')}")
                        console.print()
                        choice = Prompt.ask(t('migrate_enter_number'), default="")
                        if choice == "1":
                            sub_cmd = "file"
                        elif choice == "2":
                            sub_cmd = "online"
                        else:
                            continue

                    if sub_cmd == "online":
                        # 在线迁移向导
                        migrate_instruction = self.migrate_online_wizard()
                        if migrate_instruction:
                            user_input = migrate_instruction
                            # 继续执行，不要continue
                        else:
                            continue
                    else:
                        # 原有的文件迁移向导
                        migrate_instruction = self.migrate_wizard()
                        if migrate_instruction and self._loaded_file_content:
                            # 自动发送迁移指令
                            user_input = migrate_instruction
                            # 继续执行，不要continue
                        else:
                            continue

                # 处理 /connection 命令 (带子命令)
                if user_input.lower().startswith('/connection'):
                    parts = user_input.split(maxsplit=1)
                    args = parts[1].strip() if len(parts) > 1 else ""
                    self.handle_connection_command(args)
                    continue

                # 处理 /provider 命令 (带子命令)
                if user_input.lower().startswith('/provider'):
                    parts = user_input.split(maxsplit=1)
                    args = parts[1].strip() if len(parts) > 1 else ""
                    self.handle_provider_command(args)
                    continue

                # 处理 /session 命令 (带子命令)
                if user_input.lower().startswith('/session'):
                    parts = user_input.split(maxsplit=1)
                    args = parts[1].strip() if len(parts) > 1 else ""
                    self.handle_session_command(args)
                    continue

                # 如果有加载的文件，将文件内容作为上下文添加到消息中
                if self._loaded_file_content and not user_input.startswith('/'):
                    # 检查用户是否想要处理文件内容
                    file_context = self.get_file_context()
                    user_input = user_input + file_context
                    # 使用后清除（可选：也可以保持文件内容直到用户主动清除）
                    # self.clear_loaded_file()

                # 发送给Agent
                console.print()

                def on_thinking(event_type, data):
                    if event_type == "tool_call":
                        self.show_tool_call(data["name"], data["input"])
                    elif event_type == "tool_result":
                        self.show_tool_result(data["name"], data["result"])

                # 定义中断回调
                def on_esc_pressed():
                    self.agent.request_interrupt()
                    self._was_interrupted = True

                # 开始监听 ESC
                self.esc_listener.start(on_esc_pressed)
                self._was_interrupted = False

                console.print(f"[dim]{t('thinking')} ({t('press_esc_to_interrupt')})[/]")
                response = self.agent.chat(user_input, on_thinking=on_thinking)

                # 停止监听
                self.esc_listener.stop()

                # 检查是否被中断
                if response is None and self._was_interrupted:
                    console.print()
                    console.print(f"[yellow]{t('task_interrupted')}[/]")
                    console.print(f"[dim]{t('interrupt_hint')}[/]")
                    console.print()
                    continue

                console.print()

                # 显示响应
                if response:
                    console.print(Panel(
                        Markdown(response),
                        border_style="magenta",
                        box=box.ROUNDED,
                        padding=(1, 2)
                    ))

                # 循环检查待确认的操作（支持错误后重试生成新的待确认操作）
                while self.agent.has_pending_operations():
                    pending_ops = self.agent.get_all_pending_operations()
                    total = len(pending_ops)

                    console.print()
                    console.print(f"[yellow]{t('pending_operations', count=total)}[/]")

                    # 收集执行结果
                    execution_results = []
                    has_errors = False  # 跟踪是否有执行失败的操作
                    skip_all = False  # 跳过所有后续操作
                    execute_all = False  # 执行所有后续操作

                    for i, op in enumerate(pending_ops):
                        console.print()
                        console.print(Panel(
                            Syntax(op["sql"], "sql", theme="monokai", word_wrap=True),
                            title=f"[bold yellow]{t('pending_sql_title')} ({i+1}/{total})[/]",
                            border_style="yellow",
                            box=box.ROUNDED
                        ))

                        # 如果已选择跳过所有或执行所有，直接处理
                        if skip_all:
                            console.print(f"[dim]{t('skipped')}[/]")
                            execution_results.append(t('execution_result_skipped', index=i+1))
                            continue

                        if execute_all:
                            user_choice = "1"
                        else:
                            # 构建选项列表
                            options = [
                                ("1", t('confirm_option_execute')),
                                ("2", t('confirm_option_skip')),
                            ]
                            if total > 1:
                                options.append(("3", t('confirm_option_execute_all')))
                                options.append(("4", t('confirm_option_skip_all')))

                            # 尝试使用内联交互式选择
                            console.print()
                            result = inline_select(
                                t('confirm_select_action'),
                                options,
                                default_index=0  # 默认选中"执行"
                            )

                            if result is not None:
                                user_choice = result
                            else:
                                # Fallback: 使用数字输入
                                console.print(f"[yellow]{t('confirm_select_action')}[/]")
                                for idx, (val, label) in enumerate(options, 1):
                                    console.print(f"  [white]{idx}.[/] {label}")
                                console.print()
                                user_choice = Prompt.ask(
                                    f"[cyan]{t('input_enter_number')}[/]",
                                    choices=[str(i) for i in range(1, len(options)+1)],
                                    default="1"
                                )

                        if user_choice == "1":
                            result = self.agent.confirm_operation(i)
                            if result.get("status") == "success":
                                console.print(f"[green]{SYM_CHECK()}[/] {result.get('message', t('execute_success'))}")
                                execution_results.append(t('execution_result_success', index=i+1, message=result.get('message', '')))
                            else:
                                error_msg = result.get('error', t('error'))
                                console.print(f"[red]{SYM_CROSS()}[/] {t('execute_failed')}: {error_msg}")
                                execution_results.append(t('execution_result_failed', index=i+1, error=error_msg))
                                has_errors = True
                        elif user_choice == "2":
                            console.print(f"[dim]{t('skipped')}[/]")
                            execution_results.append(t('execution_result_skipped', index=i+1))
                        elif user_choice == "3":
                            execute_all = True
                            result = self.agent.confirm_operation(i)
                            if result.get("status") == "success":
                                console.print(f"[green]{SYM_CHECK()}[/] {result.get('message', t('execute_success'))}")
                                execution_results.append(t('execution_result_success', index=i+1, message=result.get('message', '')))
                            else:
                                error_msg = result.get('error', t('error'))
                                console.print(f"[red]{SYM_CROSS()}[/] {t('execute_failed')}: {error_msg}")
                                execution_results.append(t('execution_result_failed', index=i+1, error=error_msg))
                                has_errors = True
                        elif user_choice == "4":
                            skip_all = True
                            console.print(f"[dim]{t('skipped')}[/]")
                            execution_results.append(t('execution_result_skipped', index=i+1))

                    self.agent.clear_pending_operations()

                    # 自动发送执行结果给Agent，让它继续任务
                    if execution_results:
                        console.print()

                        # 构建反馈消息 - 根据是否有错误使用不同的提示
                        if has_errors:
                            feedback_message = t('execution_feedback_header') + "\n" + "\n".join(execution_results) + "\n\n" + t('execution_feedback_has_errors')
                        else:
                            feedback_message = t('execution_feedback_header') + "\n" + "\n".join(execution_results) + "\n\n" + t('execution_feedback_all_success')

                        # 开始监听 ESC
                        self.esc_listener.start(on_esc_pressed)
                        self._was_interrupted = False

                        console.print(f"[dim]{t('thinking')} ({t('press_esc_to_interrupt')})[/]")

                        # 继续对话
                        response = self.agent.chat(feedback_message, on_thinking=on_thinking)

                        # 停止监听
                        self.esc_listener.stop()

                        # 检查是否被中断
                        if response is None and self._was_interrupted:
                            console.print()
                            console.print(f"[yellow]{t('task_interrupted')}[/]")
                            console.print(f"[dim]{t('interrupt_hint')}[/]")
                            break  # 退出待确认操作循环

                        console.print()

                        # 显示响应
                        if response:
                            console.print(Panel(
                                Markdown(response),
                                border_style="magenta",
                                box=box.ROUNDED,
                                padding=(1, 2)
                            ))

                        # 循环将自动检查是否有新的待确认操作

                console.print()

            except KeyboardInterrupt:
                # 确保停止 ESC 监听
                self.esc_listener.stop()
                console.print()
                if Confirm.ask(f"[dim]{t('confirm_exit')}[/]", default=False):
                    self.exit_cli()
                console.print()

            except Exception as e:
                # 确保停止 ESC 监听
                self.esc_listener.stop()
                console.print()
                console.print(f"[red]{t('error')}:[/] {e}")
                console.print()


def setup_wizard(storage: SQLiteStorage) -> bool:
    """
    首次启动时的设置向导

    Args:
        storage: SQLite storage instance

    Returns:
        True if setup completed successfully
    """
    from datetime import datetime

    console.print()
    console.print(Panel(
        f"[bold cyan]{t('setup_welcome')}[/]\n\n{t('setup_first_time')}",
        border_style="cyan",
        box=box.ROUNDED
    ))
    console.print()

    # Step 1: Configure Database Connection
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
            return False
    except ValueError:
        console.print(f"[red]{t('enter_valid_number')}[/]")
        return False

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
    db_config = None
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
            if Confirm.ask(f"[yellow]{t('setup_retry_connection')}[/]", default=True):
                return setup_wizard(storage)
            return False

    # Save connection
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
        is_active=True,
        created_at=now,
        updated_at=now
    )
    storage.add_connection(conn)
    console.print(f"[green]{SYM_CHECK()}[/] {t('connection_add_success', name=conn_name)}")

    # Step 2: Configure LLM Provider
    console.print()
    console.print(f"[bold cyan]{t('setup_step_llm')}[/]")
    console.print()

    # Select provider type
    providers = LLMClientFactory.get_available_providers()
    provider_keys = list(providers.keys())

    for i, (key, name) in enumerate(providers.items(), 1):
        recommended = t('setup_provider_recommended') if key == 'deepseek' else ''
        console.print(f"  [white]{i}.[/] {name} {recommended}")

    console.print()
    choice = Prompt.ask(f"[cyan]{t('setup_select_provider')}[/]", default="1")

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(provider_keys):
            provider_type = provider_keys[idx]
        else:
            console.print(f"[red]{t('invalid_choice')}[/]")
            return False
    except ValueError:
        console.print(f"[red]{t('enter_valid_number')}[/]")
        return False

    provider_info = LLMClientFactory.PROVIDERS[provider_type]
    default_model = provider_info['default_model']

    # Collect provider details
    console.print()
    api_key = Prompt.ask(f"[cyan]{t('setup_api_key_hint', provider=provider_info['name'])}[/]", password=True)
    model = Prompt.ask(f"[cyan]{t('setup_model')} ({t('setup_model_default', model=default_model)})[/]", default=default_model)

    base_url = provider_info.get('base_url')
    if base_url:
        base_url = Prompt.ask(f"[cyan]{t('setup_base_url')} ({t('setup_base_url_hint')})[/]", default=base_url)

    # Provider name
    provider_name = Prompt.ask(f"[cyan]{t('setup_provider_name')}[/]", default=provider_type)

    # Test API
    console.print()
    with console.status(f"[dim]{t('setup_testing_api')}[/]", spinner="dots"):
        try:
            test_client = LLMClientFactory.create(
                provider=provider_type,
                api_key=api_key,
                model=model,
                base_url=base_url
            )
            console.print(f"[green]{SYM_CHECK()}[/] {t('setup_api_success')}")
        except Exception as e:
            console.print(f"[red]{SYM_CROSS()}[/] {t('setup_api_failed', error=str(e))}")
            if Confirm.ask(f"[yellow]{t('setup_retry_api')}[/]", default=True):
                # Remove the connection we just added
                storage.delete_connection(conn_name)
                return setup_wizard(storage)
            return False

    # Save provider
    provider = LLMProvider(
        id=None,
        name=provider_name,
        provider=provider_type,
        api_key_encrypted=encrypt(api_key),
        model=model,
        base_url=base_url,
        is_default=True,
        created_at=now,
        updated_at=now
    )
    storage.add_provider(provider)
    console.print(f"[green]{SYM_CHECK()}[/] {t('provider_add_success', name=provider_name)}")

    console.print()
    console.print(Panel(
        f"[bold green]{t('setup_complete')}[/]",
        border_style="green",
        box=box.ROUNDED
    ))
    console.print()

    return True


def main():
    """主函数"""
    from datetime import datetime

    # 初始化 SQLite 存储
    storage = SQLiteStorage()

    # 加载保存的语言设置
    saved_lang = storage.get_preference('language')
    if saved_lang:
        i18n.lang = saved_lang

    # 检查是否有配置
    active_conn = storage.get_active_connection()
    default_provider = storage.get_default_provider()

    # 如果没有配置，检查是否有旧的 config.ini 可以迁移
    if not active_conn or not default_provider:
        config_path = find_config_ini()

        if config_path:
            # 发现旧配置文件，提示迁移
            console.print()
            console.print(f"[yellow]{t('migrate_prompt')}[/]")
            if Confirm.ask(f"[cyan]{t('migrate_ask')}[/]", default=True):
                if migrate_from_ini(storage, config_path):
                    console.print(f"[green]{SYM_CHECK()}[/] {t('migrate_success')}")
                    # 重新获取配置
                    active_conn = storage.get_active_connection()
                    default_provider = storage.get_default_provider()
                else:
                    console.print(f"[red]{SYM_CROSS()}[/] {t('migrate_failed')}")

    # 如果仍然没有配置，启动设置向导
    if not active_conn or not default_provider:
        if not setup_wizard(storage):
            console.print(f"[red]{t('setup_incomplete')}[/]")
            sys.exit(1)
        # 重新获取配置
        active_conn = storage.get_active_connection()
        default_provider = storage.get_default_provider()

    # 使用存储的配置初始化
    db_config = {
        'type': active_conn.db_type,
        'host': active_conn.host,
        'port': active_conn.port,
        'database': active_conn.database,
        'user': active_conn.username,
        'password': decrypt(active_conn.password_encrypted),
    }

    # Session management - always create a new session on startup
    session_name = datetime.now().strftime(t("session_default_name_format"))
    session_id = storage.create_session(
        session_name,
        active_conn.id if active_conn else None,
        default_provider.id if default_provider else None
    )
    storage.set_current_session(session_id)

    # 创建LLM客户端
    with console.status(f"[dim]{t('initializing')}[/]", spinner="dots"):
        try:
            api_key = decrypt(default_provider.api_key_encrypted)
            llm_client = LLMClientFactory.create(
                provider=default_provider.provider,
                api_key=api_key,
                model=default_provider.model,
                base_url=default_provider.base_url
            )
        except Exception as e:
            console.print(f"[red]{t('init_llm_failed')}:[/] {e}")
            sys.exit(1)

        # 创建Agent with session support
        agent = SQLTuningAgent(
            llm_client=llm_client,
            db_config=db_config,
            language=i18n.lang,
            storage=storage,
            session_id=session_id
        )

    # 启动CLI
    cli = AgentCLI(agent, storage)
    cli.current_session_id = session_id
    cli.run()


if __name__ == "__main__":
    main()
