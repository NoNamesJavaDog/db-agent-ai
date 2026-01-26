"""
Configuration Manager for CLI
"""
import configparser
from db_agent.llm import LLMClientFactory


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
        return {
            "host": self.config.get('database', 'host', fallback='localhost'),
            "port": self.config.getint('database', 'port', fallback=5432),
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
