"""
Database Tools Base Class - Abstract interface for database operations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from db_agent.core.sql_analyzer import SQLAnalyzer


class BaseDatabaseTools(ABC):
    """Abstract base class for database tools"""

    def __init__(self):
        """Initialize base database tools"""
        # SQL analyzer will be initialized by subclasses after db_type is set
        self._sql_analyzer = None

    def _get_sql_analyzer(self) -> SQLAnalyzer:
        """Get SQL analyzer instance (lazy initialization)"""
        if self._sql_analyzer is None:
            self._sql_analyzer = SQLAnalyzer(self.db_type)
        return self._sql_analyzer

    def check_query_performance(self, sql: str) -> Dict[str, Any]:
        """
        检查查询性能，返回是否需要确认

        Args:
            sql: SQL语句

        Returns:
            性能检查结果，包含:
            - should_confirm: 是否需要用户确认
            - is_analytical: 是否为分析类查询
            - performance_summary: 性能摘要
            - issues: 问题列表
        """
        analyzer = self._get_sql_analyzer()

        # 检查是否为分析类查询
        if not analyzer.is_analytical_query(sql):
            return {
                "should_confirm": False,
                "is_analytical": False,
                "performance_summary": {},
                "issues": []
            }

        # 执行EXPLAIN获取执行计划
        try:
            explain_result = self.run_explain(sql, analyze=False)
        except Exception as e:
            # EXPLAIN失败时不阻止执行
            return {
                "should_confirm": False,
                "is_analytical": True,
                "performance_summary": {"error": str(e)},
                "issues": []
            }

        # 解析执行计划
        analysis = analyzer.parse_explain_output(explain_result)

        return {
            "should_confirm": analysis.get("should_confirm", False),
            "is_analytical": True,
            "performance_summary": analysis.get("performance_summary", {}),
            "issues": analysis.get("issues", [])
        }

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
