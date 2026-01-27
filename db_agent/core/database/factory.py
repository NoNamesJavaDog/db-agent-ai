"""
Database Tools Factory - Creates appropriate database tools based on type
"""
from typing import Dict, Any
from .base import BaseDatabaseTools


class DatabaseToolsFactory:
    """Factory class for creating database-specific tools"""

    SUPPORTED_TYPES = ["postgresql", "mysql"]

    @staticmethod
    def create(db_type: str, db_config: Dict[str, Any]) -> BaseDatabaseTools:
        """
        Create database tools instance based on database type

        Args:
            db_type: Database type ("postgresql" or "mysql")
            db_config: Database configuration dictionary

        Returns:
            BaseDatabaseTools instance

        Raises:
            ValueError: If database type is not supported
        """
        db_type = db_type.lower()

        if db_type == "postgresql":
            from .postgresql import PostgreSQLTools
            return PostgreSQLTools(db_config)
        elif db_type == "mysql":
            from .mysql import MySQLTools
            return MySQLTools(db_config)
        else:
            raise ValueError(
                f"Unsupported database type: {db_type}. "
                f"Supported types: {', '.join(DatabaseToolsFactory.SUPPORTED_TYPES)}"
            )

    @staticmethod
    def get_supported_types():
        """Get list of supported database types"""
        return DatabaseToolsFactory.SUPPORTED_TYPES.copy()
