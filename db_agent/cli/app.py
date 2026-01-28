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
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

from db_agent.core import SQLTuningAgent
from db_agent.llm import LLMClientFactory
from db_agent.i18n import i18n, t
from .config import ConfigManager


console = Console()


class AgentCLI:
    """AI Agent命令行界面"""

    def __init__(self, agent: SQLTuningAgent, config_manager: ConfigManager):
        self.agent = agent
        self.config_manager = config_manager

        # 斜杠命令列表 (用于自动补全)
        self.slash_commands = [
            ("/help", "cmd_help"),
            ("/file", "cmd_file"),
            ("/migrate", "cmd_migrate"),
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

        # 设置prompt_toolkit自动补全
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
                # 保存语言设置到配置文件
                self.config_manager.set_language(new_lang)
                console.print(f"[green]{SYM_CHECK()}[/] {t('language_switched')}")
            else:
                console.print(f"[red]{t('invalid_choice')}[/]")
        except ValueError:
            console.print(f"[red]{t('enter_valid_number')}[/]")

        console.print()

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

    def exit_cli(self):
        """退出CLI"""
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
                if user_input.lower() == '/migrate':
                    migrate_instruction = self.migrate_wizard()
                    if migrate_instruction and self._loaded_file_content:
                        # 自动发送迁移指令
                        user_input = migrate_instruction
                        # 继续执行，不要continue
                    else:
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

                console.print(f"[dim]{t('thinking')}[/]")
                response = self.agent.chat(user_input, on_thinking=on_thinking)
                console.print()

                # 显示响应
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

                    for i, op in enumerate(pending_ops):
                        console.print()
                        console.print(Panel(
                            Syntax(op["sql"], "sql", theme="monokai", word_wrap=True),
                            title=f"[bold yellow]{t('pending_sql_title')} ({i+1}/{total})[/]",
                            border_style="yellow",
                            box=box.ROUNDED
                        ))

                        confirm = Confirm.ask(f"[yellow]{t('confirm_execute')}[/]", default=False)

                        if confirm:
                            result = self.agent.confirm_operation(i)
                            if result.get("status") == "success":
                                console.print(f"[green]{SYM_CHECK()}[/] {result.get('message', t('execute_success'))}")
                                execution_results.append(t('execution_result_success', index=i+1, message=result.get('message', '')))
                            else:
                                error_msg = result.get('error', t('error'))
                                console.print(f"[red]{SYM_CROSS()}[/] {t('execute_failed')}: {error_msg}")
                                execution_results.append(t('execution_result_failed', index=i+1, error=error_msg))
                                has_errors = True  # 标记有错误发生
                        else:
                            console.print(f"[dim]{t('skipped')}[/]")
                            execution_results.append(t('execution_result_skipped', index=i+1))

                    self.agent.clear_pending_operations()

                    # 自动发送执行结果给Agent，让它继续任务
                    if execution_results:
                        console.print()
                        console.print(f"[dim]{t('thinking')}[/]")

                        # 构建反馈消息 - 根据是否有错误使用不同的提示
                        if has_errors:
                            feedback_message = t('execution_feedback_header') + "\n" + "\n".join(execution_results) + "\n\n" + t('execution_feedback_has_errors')
                        else:
                            feedback_message = t('execution_feedback_header') + "\n" + "\n".join(execution_results) + "\n\n" + t('execution_feedback_all_success')

                        # 继续对话
                        response = self.agent.chat(feedback_message, on_thinking=on_thinking)
                        console.print()

                        # 显示响应
                        console.print(Panel(
                            Markdown(response),
                            border_style="magenta",
                            box=box.ROUNDED,
                            padding=(1, 2)
                        ))

                        # 循环将自动检查是否有新的待确认操作

                console.print()

            except KeyboardInterrupt:
                console.print()
                if Confirm.ask(f"[dim]{t('confirm_exit')}[/]", default=False):
                    self.exit_cli()
                console.print()

            except Exception as e:
                console.print()
                console.print(f"[red]{t('error')}:[/] {e}")
                console.print()


def main():
    """主函数"""
    # 查找配置文件路径
    # 首先尝试新位置 config/config.ini
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(script_dir, 'config', 'config.ini')

    # 如果新位置不存在，尝试旧位置
    if not os.path.exists(config_path):
        config_path = os.path.join(script_dir, 'config.ini')

    if not os.path.exists(config_path):
        console.print(Panel(
            f"[red]{t('config_not_found')}[/]",
            title=f"[bold red]{t('error')}[/]",
            border_style="red"
        ))
        sys.exit(1)

    config_manager = ConfigManager(config_path)

    # 加载保存的语言设置
    saved_lang = config_manager.get_language()
    if saved_lang:
        i18n.lang = saved_lang

    # 获取数据库配置
    db_config = config_manager.get_db_config()

    # 获取默认提供商
    default_provider = config_manager.get_default_provider()
    provider_config = config_manager.get_provider_config(default_provider)

    if not provider_config or not provider_config.get("api_key"):
        console.print(f"[red]{t('error')}:[/] {t('api_key_not_configured', provider=default_provider)}")
        sys.exit(1)

    # 创建LLM客户端
    with console.status(f"[dim]{t('initializing')}[/]", spinner="dots"):
        try:
            llm_client = LLMClientFactory.create(
                provider=default_provider,
                api_key=provider_config["api_key"],
                model=provider_config.get("model"),
                base_url=provider_config.get("base_url")
            )
        except Exception as e:
            console.print(f"[red]{t('init_llm_failed')}:[/] {e}")
            sys.exit(1)

        # 创建Agent
        agent = SQLTuningAgent(
            llm_client=llm_client,
            db_config=db_config,
            language=i18n.lang
        )

    # 启动CLI
    cli = AgentCLI(agent, config_manager)
    cli.run()


if __name__ == "__main__":
    main()
