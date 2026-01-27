"""
Database Tools Base Class - Abstract interface for database operations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseDatabaseTools(ABC):
    """Abstract base class for database tools"""

    @abstractmethod
    def get_connection(self):
        """Get database connection"""
        pass

    @abstractmethod
    def get_db_info(self) -> Dict[str, Any]:
        """Get database information"""
        pass

    @abstractmethod
    def list_tables(self, schema: str = None) -> Dict[str, Any]:
        """List all tables in the database"""
        pass

    @abstractmethod
    def describe_table(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """Get table structure information"""
        pass

    @abstractmethod
    def execute_sql(self, sql: str, confirmed: bool = False) -> Dict[str, Any]:
        """Execute any SQL statement (INSERT/UPDATE/DELETE/CREATE/ALTER/DROP etc.)"""
        pass

    @abstractmethod
    def execute_safe_query(self, sql: str) -> Dict[str, Any]:
        """Execute safe read-only SELECT query"""
        pass

    @abstractmethod
    def run_explain(self, sql: str, analyze: bool = False) -> Dict[str, Any]:
        """Run EXPLAIN to analyze SQL execution plan"""
        pass

    @abstractmethod
    def identify_slow_queries(self, min_duration_ms: float = 1000, limit: int = 20) -> Dict[str, Any]:
        """Identify slow queries in the database"""
        pass

    @abstractmethod
    def get_running_queries(self) -> Dict[str, Any]:
        """Get currently running queries"""
        pass

    @abstractmethod
    def check_index_usage(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """Check index usage for a table"""
        pass

    @abstractmethod
    def get_table_stats(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """Get table statistics"""
        pass

    @abstractmethod
    def create_index(self, index_sql: str, concurrent: bool = True) -> Dict[str, Any]:
        """Create an index"""
        pass

    @abstractmethod
    def analyze_table(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """Update table statistics (ANALYZE)"""
        pass

    @abstractmethod
    def get_sample_data(self, table_name: str, schema: str = None, limit: int = 10) -> Dict[str, Any]:
        """Get sample data from a table"""
        pass

    @property
    @abstractmethod
    def db_type(self) -> str:
        """Return the database type identifier (e.g., 'postgresql', 'mysql')"""
        pass
