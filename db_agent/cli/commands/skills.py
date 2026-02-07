"""
Skills Management Commands Mixin

Provides methods for managing skills:
show, reload, execute.
"""
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

from db_agent.cli.ui import console, SYM_CHECK
from db_agent.i18n import t

try:
    from prompt_toolkit.completion import WordCompleter
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


class SkillsCommandsMixin:
    """Mixin for skills management commands.

    Expects the host class to provide:
        self.agent              - SQLTuningAgent instance
        self.skill_registry     - SkillRegistry instance
        self.skill_executor     - SkillExecutor instance
        self.current_session_id - Current session ID
        self.slash_commands     - List of slash commands
        self.command_completer  - WordCompleter (if prompt_toolkit available)
        self.show_tool_call()   - Method to display tool calls
        self.show_tool_result() - Method to display tool results
    """

    def handle_skills_command(self, args: str):
        """Handle /skills sub-commands"""
        parts = args.strip().split(maxsplit=1)
        if not parts:
            self.show_skills()
            return

        subcommand = parts[0].lower()

        if subcommand == "list":
            self.show_skills()
        elif subcommand == "reload":
            self.reload_skills()
        else:
            console.print(f"[red]{t('invalid_choice')}[/]")

    def show_skills(self):
        """Show skills list"""
        console.print()
        skills = self.skill_registry.list_all()

        if not skills:
            console.print(f"[dim]{t('skills_empty')}[/]")
            console.print()
            console.print(f"[dim]{t('skill_list_hint')}[/]")
            console.print()
            return

        table = Table(box=box.ROUNDED, padding=(0, 2))
        table.add_column("#", style="cyan", justify="center", width=3)
        table.add_column(t("skill_name"), style="green")
        table.add_column(t("skill_description"), style="white")
        table.add_column(t("skill_source"), style="dim")

        for i, skill in enumerate(skills, 1):
            source = t("skill_source_personal") if skill.source == "personal" else t("skill_source_project")
            desc = skill.description or ""
            if len(desc) > 50:
                desc = desc[:50] + "..."
            table.add_row(
                str(i),
                f"/{skill.name}",
                desc,
                source
            )

        console.print(Panel(
            table,
            title=f"[bold cyan]{t('skills_title')}[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        console.print()
        console.print(f"[dim]{t('skill_list_hint')}[/]")
        console.print()

    def reload_skills(self):
        """Reload skills"""
        self.skill_registry.reload()
        count = self.skill_registry.count

        # Update autocomplete
        if PROMPT_TOOLKIT_AVAILABLE:
            all_commands = [cmd for cmd, _ in self.slash_commands]
            all_commands.extend(self.skill_registry.get_user_invocable_names())
            self.command_completer = WordCompleter(
                all_commands,
                ignore_case=True,
                match_middle=False
            )

        # Refresh system prompt to include updated skills descriptions
        self.agent.refresh_system_prompt()

        console.print(f"[green]{SYM_CHECK()}[/] {t('skills_reloaded')} ({t('skills_loaded', count=count)})")

    def execute_skill(self, skill_name: str, arguments: str = ""):
        """
        Execute a skill.

        Args:
            skill_name: Skill name (without / prefix)
            arguments: Arguments to pass to the skill
        """
        skill = self.skill_registry.get(skill_name)
        if not skill:
            console.print(f"[red]{t('skill_not_found', name=skill_name)}[/]")
            return

        # Execute the skill
        context = {
            "session_id": str(self.current_session_id) if self.current_session_id else "",
        }
        result = self.skill_executor.execute(skill_name, arguments, context)

        if result.get("status") == "error":
            console.print(f"[red]{t('skill_execute_failed', name=skill_name, error=result.get('error', 'Unknown error'))}[/]")
            return

        # Get the processed instructions and send to agent
        instructions = result.get("instructions", "")
        if instructions:
            console.print()
            console.print(f"[dim]{t('skill_executed', name=skill_name)}[/]")
            console.print()

            # Send instructions to agent as user message
            def on_thinking(event_type, data):
                if event_type == "tool_call":
                    self.show_tool_call(data["name"], data["input"])
                elif event_type == "tool_result":
                    self.show_tool_result(data["name"], data["result"])

            console.print(f"[dim]{t('thinking')}[/]")
            response = self.agent.chat(instructions, on_thinking=on_thinking)

            console.print()

            if response:
                console.print(Panel(
                    Markdown(response),
                    border_style="magenta",
                    box=box.ROUNDED,
                    padding=(1, 2)
                ))
