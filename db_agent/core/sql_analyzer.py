"""
SQL Analyzer - SQL性能分析器
用于在执行分析类查询前检查SQL性能问题
"""
import re
from typing import Dict, Any, List, Tuple
from enum import Enum


class IssueLevel(Enum):
    """问题级别"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class SQLAnalyzer:
    """SQL分析器 - 判断是否为分析类查询并检测性能问题"""

    # 分析类查询的关键词模式
    ANALYTICAL_PATTERNS = [
        r'\bJOIN\b',
        r'\bLEFT\s+JOIN\b',
        r'\bRIGHT\s+JOIN\b',
        r'\bINNER\s+JOIN\b',
        r'\bOUTER\s+JOIN\b',
        r'\bCROSS\s+JOIN\b',
        r'\bGROUP\s+BY\b',
        r'\bORDER\s+BY\b',
        r'\bDISTINCT\b',
        r'\bUNION\b',
        r'\bINTERSECT\b',
        r'\bEXCEPT\b',
        r'\bWITH\s+\w+\s+AS\b',  # CTE
        r'\bOVER\s*\(',  # 窗口函数
        r'\bROW_NUMBER\s*\(',
        r'\bRANK\s*\(',
        r'\bDENSE_RANK\s*\(',
        r'\bLAG\s*\(',
        r'\bLEAD\s*\(',
        r'\bSUM\s*\(',
        r'\bCOUNT\s*\(',
        r'\bAVG\s*\(',
        r'\bMIN\s*\(',
        r'\bMAX\s*\(',
    ]

    # 性能问题阈值
    THRESHOLDS = {
        "full_scan_rows": 10000,      # 全表扫描行数阈值（CRITICAL）
        "large_rows": 100000,          # 预估行数过大阈值（WARNING）
        "high_cost": 10000,            # 执行cost过高阈值（WARNING）
        "nested_loop_rows": 1000,      # 嵌套循环外层行数阈值（WARNING）
    }

    def __init__(self, db_type: str = "postgresql"):
        """
        初始化SQL分析器

        Args:
            db_type: 数据库类型 (postgresql/mysql/gaussdb/oracle)
        """
        self.db_type = db_type.lower()

    def is_analytical_query(self, sql: str) -> bool:
        """
        判断SQL是否为分析类查询

        Args:
            sql: SQL语句

        Returns:
            是否为分析类查询
        """
        sql_upper = sql.upper()

        # 必须是SELECT查询
        if not sql_upper.strip().startswith("SELECT"):
            return False

        # 检查是否包含分析类关键词
        for pattern in self.ANALYTICAL_PATTERNS:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return True

        # 检查是否包含子查询
        if self._has_subquery(sql):
            return True

        # 检查是否为无WHERE且无LIMIT的全表查询
        if self._is_full_table_scan_without_filter(sql_upper):
            return True

        return False

    def _has_subquery(self, sql: str) -> bool:
        """检查是否包含子查询"""
        # 简单检测：SELECT 在 FROM 或 WHERE 子句中出现
        sql_upper = sql.upper()
        # 移除字符串字面量以避免误判
        cleaned_sql = re.sub(r"'[^']*'", "''", sql_upper)
        cleaned_sql = re.sub(r'"[^"]*"', '""', cleaned_sql)

        # 统计 SELECT 出现次数
        select_count = len(re.findall(r'\bSELECT\b', cleaned_sql))
        return select_count > 1

    def _is_full_table_scan_without_filter(self, sql_upper: str) -> bool:
        """检查是否为无WHERE且无LIMIT的全表查询"""
        has_where = re.search(r'\bWHERE\b', sql_upper)
        has_limit = re.search(r'\bLIMIT\b', sql_upper)
        has_top = re.search(r'\bTOP\s+\d+\b', sql_upper)  # SQL Server 风格

        return not has_where and not has_limit and not has_top

    def parse_explain_output(self, explain_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析EXPLAIN输出，检测性能问题

        Args:
            explain_result: run_explain返回的结果

        Returns:
            性能分析结果
        """
        issues = []
        performance_summary = {}

        if explain_result.get("status") != "success":
            return {
                "has_issues": False,
                "issues": [],
                "performance_summary": {"error": explain_result.get("error", "Unknown error")},
                "should_confirm": False
            }

        plan = explain_result.get("plan", [])
        if not plan:
            return {
                "has_issues": False,
                "issues": [],
                "performance_summary": {},
                "should_confirm": False
            }

        # 根据数据库类型解析
        if self.db_type in ("postgresql", "gaussdb"):
            issues, performance_summary = self._parse_postgresql_plan(plan)
        elif self.db_type == "mysql":
            issues, performance_summary = self._parse_mysql_plan(plan)
        elif self.db_type == "oracle":
            issues, performance_summary = self._parse_oracle_plan(plan)
        else:
            issues, performance_summary = self._parse_postgresql_plan(plan)

        # 判断是否需要确认
        has_critical = any(issue["level"] == IssueLevel.CRITICAL.value for issue in issues)

        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "performance_summary": performance_summary,
            "should_confirm": has_critical
        }

    def _parse_postgresql_plan(self, plan: List[str]) -> Tuple[List[Dict], Dict]:
        """
        解析PostgreSQL/GaussDB的EXPLAIN输出

        Args:
            plan: EXPLAIN输出的行列表

        Returns:
            (issues, performance_summary)
        """
        issues = []
        performance_summary = {
            "scan_types": [],
            "total_cost": None,
            "estimated_rows": None
        }

        plan_text = "\n".join(plan) if isinstance(plan, list) else str(plan)

        # 提取总cost
        cost_match = re.search(r'cost=[\d.]+\.\.([\d.]+)', plan_text)
        if cost_match:
            total_cost = float(cost_match.group(1))
            performance_summary["total_cost"] = total_cost
            if total_cost > self.THRESHOLDS["high_cost"]:
                issues.append({
                    "level": IssueLevel.WARNING.value,
                    "type": "high_cost",
                    "message": f"执行成本过高: {total_cost:.0f}",
                    "suggestion": "考虑添加索引或优化查询条件"
                })

        # 检测全表扫描 (Seq Scan)
        seq_scan_pattern = r'Seq Scan on (\w+).*?rows=(\d+)'
        for match in re.finditer(seq_scan_pattern, plan_text, re.IGNORECASE | re.DOTALL):
            table_name = match.group(1)
            rows = int(match.group(2))
            performance_summary["scan_types"].append(f"Seq Scan on {table_name}")

            if rows > self.THRESHOLDS["full_scan_rows"]:
                issues.append({
                    "level": IssueLevel.CRITICAL.value,
                    "type": "full_table_scan",
                    "table": table_name,
                    "rows": rows,
                    "message": f"表 {table_name} 全表扫描，预估扫描 {rows:,} 行",
                    "suggestion": "为查询条件列添加索引"
                })

        # 检测预估行数过大
        rows_pattern = r'rows=(\d+)'
        max_rows = 0
        for match in re.finditer(rows_pattern, plan_text):
            rows = int(match.group(1))
            max_rows = max(max_rows, rows)

        performance_summary["estimated_rows"] = max_rows
        if max_rows > self.THRESHOLDS["large_rows"]:
            # 只有在没有全表扫描CRITICAL问题时才添加这个WARNING
            if not any(i["type"] == "full_table_scan" for i in issues):
                issues.append({
                    "level": IssueLevel.WARNING.value,
                    "type": "large_result_set",
                    "rows": max_rows,
                    "message": f"预估结果集过大: {max_rows:,} 行",
                    "suggestion": "考虑添加更多过滤条件或使用LIMIT限制结果数量"
                })

        # 检测嵌套循环
        nested_loop_pattern = r'Nested Loop.*?rows=(\d+)'
        for match in re.finditer(nested_loop_pattern, plan_text, re.IGNORECASE | re.DOTALL):
            rows = int(match.group(1))
            if rows > self.THRESHOLDS["nested_loop_rows"]:
                issues.append({
                    "level": IssueLevel.WARNING.value,
                    "type": "nested_loop",
                    "rows": rows,
                    "message": f"嵌套循环连接外层行数较大: {rows:,} 行",
                    "suggestion": "考虑使用Hash Join或Merge Join，或为关联列添加索引"
                })

        return issues, performance_summary

    def _parse_mysql_plan(self, plan: List[Any]) -> Tuple[List[Dict], Dict]:
        """
        解析MySQL的EXPLAIN输出

        Args:
            plan: EXPLAIN输出（通常是字典列表）

        Returns:
            (issues, performance_summary)
        """
        issues = []
        performance_summary = {
            "scan_types": [],
            "total_rows": 0
        }

        # MySQL EXPLAIN 返回的是行列表
        if not plan:
            return issues, performance_summary

        for row in plan:
            if isinstance(row, dict):
                table = row.get("table", "unknown")
                access_type = row.get("type", "").upper()
                rows = row.get("rows", 0) or 0
                extra = row.get("Extra", "") or ""

                performance_summary["total_rows"] += rows
                performance_summary["scan_types"].append(f"{access_type} on {table}")

                # 检测全表扫描 (ALL)
                if access_type == "ALL" and rows > self.THRESHOLDS["full_scan_rows"]:
                    issues.append({
                        "level": IssueLevel.CRITICAL.value,
                        "type": "full_table_scan",
                        "table": table,
                        "rows": rows,
                        "message": f"表 {table} 全表扫描 (type=ALL)，预估扫描 {rows:,} 行",
                        "suggestion": "为查询条件列添加索引"
                    })

                # 检测索引全扫描
                elif access_type == "INDEX" and rows > self.THRESHOLDS["full_scan_rows"]:
                    issues.append({
                        "level": IssueLevel.WARNING.value,
                        "type": "index_scan",
                        "table": table,
                        "rows": rows,
                        "message": f"表 {table} 索引全扫描 (type=INDEX)，扫描 {rows:,} 行",
                        "suggestion": "考虑优化查询条件以使用更精确的索引查找"
                    })

                # 检测 Using filesort
                if "Using filesort" in extra and rows > self.THRESHOLDS["nested_loop_rows"]:
                    issues.append({
                        "level": IssueLevel.WARNING.value,
                        "type": "filesort",
                        "table": table,
                        "message": f"表 {table} 使用文件排序 (filesort)，数据量 {rows:,} 行",
                        "suggestion": "考虑为ORDER BY列添加索引"
                    })

                # 检测 Using temporary
                if "Using temporary" in extra:
                    issues.append({
                        "level": IssueLevel.WARNING.value,
                        "type": "temporary_table",
                        "table": table,
                        "message": f"表 {table} 使用临时表",
                        "suggestion": "考虑优化GROUP BY或DISTINCT操作"
                    })

        # 检测预估行数过大
        if performance_summary["total_rows"] > self.THRESHOLDS["large_rows"]:
            if not any(i["type"] == "full_table_scan" for i in issues):
                issues.append({
                    "level": IssueLevel.WARNING.value,
                    "type": "large_result_set",
                    "rows": performance_summary["total_rows"],
                    "message": f"预估处理行数过大: {performance_summary['total_rows']:,} 行",
                    "suggestion": "考虑添加更多过滤条件或使用LIMIT限制结果数量"
                })

        return issues, performance_summary

    def _parse_oracle_plan(self, plan: List[str]) -> Tuple[List[Dict], Dict]:
        """
        解析Oracle的DBMS_XPLAN输出

        Args:
            plan: DBMS_XPLAN输出的行列表

        Returns:
            (issues, performance_summary)
        """
        issues = []
        performance_summary = {
            "scan_types": [],
            "total_cost": None,
            "estimated_rows": None
        }

        plan_text = "\n".join(plan) if isinstance(plan, list) else str(plan)

        # 提取总cost (Oracle格式: Cost (%CPU): 123 (0))
        cost_match = re.search(r'Cost\s*\(%CPU\):\s*(\d+)', plan_text)
        if cost_match:
            total_cost = float(cost_match.group(1))
            performance_summary["total_cost"] = total_cost
            if total_cost > self.THRESHOLDS["high_cost"]:
                issues.append({
                    "level": IssueLevel.WARNING.value,
                    "type": "high_cost",
                    "message": f"执行成本过高: {total_cost:.0f}",
                    "suggestion": "考虑添加索引或优化查询条件"
                })

        # 检测全表扫描 (TABLE ACCESS FULL)
        full_scan_pattern = r'TABLE ACCESS FULL\s*\|\s*(\w+)'
        for match in re.finditer(full_scan_pattern, plan_text, re.IGNORECASE):
            table_name = match.group(1)
            performance_summary["scan_types"].append(f"TABLE ACCESS FULL on {table_name}")

            # 尝试提取行数
            rows = 0
            rows_match = re.search(rf'{table_name}.*?Rows:\s*(\d+)', plan_text, re.IGNORECASE | re.DOTALL)
            if rows_match:
                rows = int(rows_match.group(1))

            if rows > self.THRESHOLDS["full_scan_rows"]:
                issues.append({
                    "level": IssueLevel.CRITICAL.value,
                    "type": "full_table_scan",
                    "table": table_name,
                    "rows": rows,
                    "message": f"表 {table_name} 全表扫描 (TABLE ACCESS FULL)，预估扫描 {rows:,} 行",
                    "suggestion": "为查询条件列添加索引"
                })
            elif rows == 0:
                # 没有行数信息，但仍然是全表扫描
                issues.append({
                    "level": IssueLevel.WARNING.value,
                    "type": "full_table_scan",
                    "table": table_name,
                    "message": f"表 {table_name} 全表扫描 (TABLE ACCESS FULL)",
                    "suggestion": "为查询条件列添加索引"
                })

        # 检测索引全扫描 (INDEX FULL SCAN)
        idx_full_scan_pattern = r'INDEX FULL SCAN\s*\|\s*(\w+)'
        for match in re.finditer(idx_full_scan_pattern, plan_text, re.IGNORECASE):
            index_name = match.group(1)
            performance_summary["scan_types"].append(f"INDEX FULL SCAN on {index_name}")
            issues.append({
                "level": IssueLevel.WARNING.value,
                "type": "index_full_scan",
                "index": index_name,
                "message": f"索引全扫描 (INDEX FULL SCAN) on {index_name}",
                "suggestion": "考虑优化查询条件以使用更精确的索引查找"
            })

        # 检测嵌套循环 (NESTED LOOPS)
        nested_loop_pattern = r'NESTED LOOPS'
        if re.search(nested_loop_pattern, plan_text, re.IGNORECASE):
            # 尝试获取相关行数
            rows_pattern = r'Rows:\s*(\d+)'
            rows_matches = re.findall(rows_pattern, plan_text)
            max_rows = max([int(r) for r in rows_matches]) if rows_matches else 0

            if max_rows > self.THRESHOLDS["nested_loop_rows"]:
                issues.append({
                    "level": IssueLevel.WARNING.value,
                    "type": "nested_loop",
                    "rows": max_rows,
                    "message": f"嵌套循环连接 (NESTED LOOPS)，涉及较大数据量: {max_rows:,} 行",
                    "suggestion": "考虑使用Hash Join，或为关联列添加索引"
                })

        # 检测排序操作 (SORT)
        sort_pattern = r'SORT\s+(ORDER BY|GROUP BY|AGGREGATE|UNIQUE)'
        for match in re.finditer(sort_pattern, plan_text, re.IGNORECASE):
            sort_type = match.group(1)
            issues.append({
                "level": IssueLevel.INFO.value,
                "type": "sort_operation",
                "message": f"排序操作 (SORT {sort_type})",
                "suggestion": "如果数据量较大，考虑添加索引以避免排序"
            })

        # 提取预估行数
        rows_pattern = r'Rows:\s*(\d+)'
        all_rows = re.findall(rows_pattern, plan_text)
        if all_rows:
            max_rows = max([int(r) for r in all_rows])
            performance_summary["estimated_rows"] = max_rows
            if max_rows > self.THRESHOLDS["large_rows"]:
                if not any(i["type"] == "full_table_scan" for i in issues):
                    issues.append({
                        "level": IssueLevel.WARNING.value,
                        "type": "large_result_set",
                        "rows": max_rows,
                        "message": f"预估结果集过大: {max_rows:,} 行",
                        "suggestion": "考虑添加更多过滤条件或使用分页限制结果数量"
                    })

        return issues, performance_summary

    def format_issues_for_display(self, issues: List[Dict], language: str = "zh") -> str:
        """
        格式化问题列表用于显示

        Args:
            issues: 问题列表
            language: 语言 (zh/en)

        Returns:
            格式化的字符串
        """
        if not issues:
            return ""

        critical_issues = [i for i in issues if i["level"] == IssueLevel.CRITICAL.value]
        warning_issues = [i for i in issues if i["level"] == IssueLevel.WARNING.value]

        lines = []

        if critical_issues:
            if language == "zh":
                lines.append(f"⚠️ 发现 {len(critical_issues)} 个严重问题:")
            else:
                lines.append(f"⚠️ Found {len(critical_issues)} critical issue(s):")
            for issue in critical_issues:
                lines.append(f"  - {issue['message']}")
                lines.append(f"    建议: {issue['suggestion']}" if language == "zh"
                           else f"    Suggestion: {issue['suggestion']}")

        if warning_issues:
            if language == "zh":
                lines.append(f"⚡ 发现 {len(warning_issues)} 个警告:")
            else:
                lines.append(f"⚡ Found {len(warning_issues)} warning(s):")
            for issue in warning_issues:
                lines.append(f"  - {issue['message']}")
                lines.append(f"    建议: {issue['suggestion']}" if language == "zh"
                           else f"    Suggestion: {issue['suggestion']}")

        return "\n".join(lines)
