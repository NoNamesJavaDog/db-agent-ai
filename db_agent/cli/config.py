"""
Configuration Manager for CLI
"""
import configparser
import os
from datetime import datetime
from typing import Optional

from db_agent.llm import LLMClientFactory


def migrate_from_ini(storage, config_path: str) -> bool:
    """
    Migrate configuration from config.ini to SQLite storage.

    Args:
        storage: SQLiteStorage instance
        config_path: Path to config.ini file

    Returns:
        True if migration was successful
    """
    from db_agent.storage import DatabaseConnection, LLMProvider, encrypt

    if not os.path.exists(config_path):
        return False

    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')

    migrated_connection = False
    migrated_provider = False

    # Migrate database connection
    if config.has_section('database'):
        db_type = config.get('database', 'type', fallback='postgresql')

        default_ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'gaussdb': 5432,
            'oracle': 1521,
            'sqlserver': 1433
        }
        default_port = default_ports.get(db_type, 5432)

        host = config.get('database', 'host', fallback='localhost')
        port = config.getint('database', 'port', fallback=default_port)
        database = config.get('database', 'database', fallback='postgres')
        user = config.get('database', 'user', fallback='postgres')
        password = config.get('database', 'password', fallback='')

        # Create connection with a default name
        conn_name = f"{db_type}_{host}_{database}"

        # Check if this connection already exists
        existing = storage.get_connection(conn_name)
        if not existing and password:
            now = datetime.now()
            conn = DatabaseConnection(
                id=None,
                name=conn_name,
                db_type=db_type,
                host=host,
                port=port,
                database=database,
                username=user,
                password_encrypted=encrypt(password),
                is_active=True,
                created_at=now,
                updated_at=now
            )
            storage.add_connection(conn)
            migrated_connection = True

    # Migrate LLM providers
    default_provider = config.get('llm', 'default_provider', fallback='deepseek')

    for provider_key in LLMClientFactory.PROVIDERS.keys():
        if config.has_section(provider_key):
            api_key = config.get(provider_key, 'api_key', fallback=None)

            # Skip placeholder API keys
            if api_key and api_key != f"your-{provider_key}-api-key":
                model = config.get(provider_key, 'model', fallback=None)
                base_url = config.get(provider_key, 'base_url', fallback=None)

                # Use provider type as default model if not specified
                if not model:
                    model = LLMClientFactory.PROVIDERS[provider_key]['default_model']

                # Create provider name (use provider key as name)
                provider_name = provider_key

                # Check if this provider already exists
                existing = storage.get_provider(provider_name)
                if not existing:
                    now = datetime.now()
                    provider = LLMProvider(
                        id=None,
                        name=provider_name,
                        provider=provider_key,
                        api_key_encrypted=encrypt(api_key),
                        model=model,
                        base_url=base_url,
                        is_default=(provider_key == default_provider),
                        created_at=now,
                        updated_at=now
                    )
                    storage.add_provider(provider)
                    migrated_provider = True

    # Migrate language preference
    lang = config.get('preferences', 'language', fallback=None)
    if lang:
        storage.set_preference('language', lang)

    return migrated_connection or migrated_provider


def find_config_ini() -> Optional[str]:
    """
    Find config.ini file in common locations.

    Returns:
        Path to config.ini or None if not found
    """
    import sys

    # Get script directory
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Check common locations
    locations = [
        os.path.join(script_dir, 'config', 'config.ini'),
        os.path.join(script_dir, 'config.ini'),
        os.path.join(os.getcwd(), 'config', 'config.ini'),
        os.path.join(os.getcwd(), 'config.ini'),
    ]

    for path in locations:
        if os.path.exists(path):
            return path

    return None


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')

    def get_language(self) -> str:
        """获取保存的语言设置"""
        return self.config.get('preferences', 'language', fallback=None)

    def set_language(self, lang: str):
        """保存语言设置"""
        if not self.config.has_section('preferences'):
            self.config.add_section('preferences')
        self.config.set('preferences', 'language', lang)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get_db_config(self) -> dict:
        """获取数据库配置"""
        db_type = self.config.get('database', 'type', fallback='postgresql')

        # Default ports for different database types
        default_ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'gaussdb': 5432  # GaussDB uses same default port as PostgreSQL
        }
        default_port = default_ports.get(db_type, 5432)

        return {
            "type": db_type,
            "host": self.config.get('database', 'host', fallback='localhost'),
            "port": self.config.getint('database', 'port', fallback=default_port),
            "database": self.config.get('database', 'database', fallback='postgres'),
            "user": self.config.get('database', 'user', fallback='postgres'),
            "password": self.config.get('database', 'password', fallback='password')
        }

    def get_default_provider(self) -> str:
        """获取默认提供商"""
        return self.config.get('llm', 'default_provider', fallback='deepseek')

    def get_provider_config(self, provider: str) -> dict:
        """获取提供商配置"""
        if not self.config.has_section(provider):
            return None

        result = {
            "api_key": self.config.get(provider, 'api_key', fallback=None),
            "model": self.config.get(provider, 'model', fallback=None),
            "base_url": self.config.get(provider, 'base_url', fallback=None)
        }
        return result

    def get_configured_providers(self) -> list:
        """获取已配置的提供商列表"""
        providers = []
        for provider in LLMClientFactory.PROVIDERS.keys():
            if self.config.has_section(provider):
                api_key = self.config.get(provider, 'api_key', fallback=None)
                if api_key and api_key != f"your-{provider}-api-key":
                    providers.append(provider)
        return providers
