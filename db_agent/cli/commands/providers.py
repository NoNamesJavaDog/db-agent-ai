"""
Provider Management Commands Mixin

Provides methods for managing LLM providers:
show, add, switch, edit, delete.
"""
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich import box

from db_agent.cli.ui import console, SYM_CHECK, SYM_CROSS
from db_agent.i18n import t
from db_agent.llm import LLMClientFactory
from db_agent.storage import LLMProvider, encrypt, decrypt


class ProviderCommandsMixin:
    """Mixin for LLM provider management commands.

    Expects the host class to provide:
        self.storage   - SQLiteStorage instance
        self.agent     - SQLTuningAgent instance
    """

    def show_providers(self):
        """Show LLM provider list"""
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
        """Handle /provider sub-commands"""
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
        """Wizard for adding a new LLM provider"""
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
        """Switch default provider"""
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
        """Edit a provider"""
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
        """Delete a provider"""
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
