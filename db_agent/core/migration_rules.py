"""
Database Migration Rules - 异构数据库迁移规则
Contains syntax mappings and conversion rules between different databases
"""

# Oracle to GaussDB Migration Rules
ORACLE_TO_GAUSSDB_RULES = {
    "description": "Oracle to GaussDB (openGauss) Migration Rules",
    "version": "1.0",

    # 高级包映射
    "packages": {
        "DBMS_LOB": {
            "target": "DBE_LOB",
            "notes": "函数名前缀变更，部分BFILE接口不支持",
            "unsupported": ["CLOB2FILE"],
            "examples": [
                ("DBMS_LOB.GETLENGTH(clob_col)", "DBE_LOB.GETLENGTH(clob_col)"),
                ("DBMS_LOB.SUBSTR(clob_col, 100, 1)", "DBE_LOB.SUBSTR(clob_col, 100, 1)"),
            ]
        },
        "DBMS_OUTPUT": {
            "target": "DBE_OUTPUT",
            "notes": "接口由存储过程变为函数，PUT/PUT_LINE处理UTF8转换时行为有细微差别",
            "examples": [
                ("DBMS_OUTPUT.PUT_LINE('text')", "DBE_OUTPUT.PUT_LINE('text')"),
            ]
        },
        "DBMS_RANDOM": {
            "target": "DBE_RANDOM",
            "notes": "不支持INITIALIZE/NORMAL/RANDOM等旧接口",
            "unsupported": ["INITIALIZE", "NORMAL", "RANDOM"],
            "mappings": {
                "SEED": "SET_SEED",
                "VALUE": "GET_VALUE",
            },
            "examples": [
                ("DBMS_RANDOM.VALUE", "DBE_RANDOM.GET_VALUE"),
                ("DBMS_RANDOM.VALUE(1, 100)", "DBE_RANDOM.GET_VALUE(1, 100)"),
            ]
        },
        "UTL_RAW": {
            "target": "DBE_RAW",
            "notes": "某些类型转换函数名变长且更明确",
            "mappings": {
                "CAST_FROM_NUMBER": "CAST_FROM_NUMBER_TO_RAW",
                "CAST_TO_NUMBER": "CAST_TO_NUMBER_FROM_RAW",
            }
        },
        "DBMS_SQL": {
            "target": "DBE_SQL",
            "notes": "接口名称基本对齐，但部分功能参数类型有变",
            "mappings": {
                "OPEN_CURSOR": "REGISTER_CONTEXT",
            }
        },
    },

    # 数据类型映射
    "data_types": {
        "NUMBER": {
            "target": "NUMBER",
            "notes": "GaussDB不支持负数标度s，需手动ROUND或TRUNC处理",
            "warnings": ["负数标度NUMBER(p,-s)需改写为手动ROUND处理"]
        },
        "VARCHAR2": {
            "target": "VARCHAR2",
            "notes": "GaussDB仅支持BYTE单位，不支持CHAR单位，最大支持10MB",
            "transform": "VARCHAR2(n CHAR) → VARCHAR2(n*4)  -- 按UTF8最大字节估算"
        },
        "DATE": {
            "target": "TIMESTAMP(0)",
            "notes": "GaussDB内部将DATE替换为不带时区的TIMESTAMP(0)，注意秒以下精度丢失",
            "warnings": ["Oracle DATE包含时间，GaussDB会转为TIMESTAMP(0)"]
        },
        "CLOB": {
            "target": "CLOB",
            "notes": "GaussDB不支持Oracle的定位器概念，避免使用依赖LOB定位器的PL/SQL操作"
        },
        "BLOB": {
            "target": "BLOB",
            "notes": "同CLOB，不支持定位器概念"
        },
        "BINARY_DOUBLE": {
            "target": "FLOAT8",
            "notes": "精度处理需注意"
        },
        "BINARY_FLOAT": {
            "target": "FLOAT4",
            "notes": "精度处理需注意"
        },
    },

    # 单行函数差异
    "functions": {
        "MOD": {
            "notes": "返回类型不一致，Oracle含BINARY_DOUBLE，GaussDB为INT或NUMERIC",
            "suggestion": "大数据量计算前显式转换类型"
        },
        "ROUND": {
            "notes": "处理NULL值逻辑不同，GaussDB仅返回FLOAT8或NUMERIC",
            "warnings": ["SELECT ROUND(NULL, 'q') 在Oracle返回NULL，GaussDB报错"]
        },
        "CHR": {
            "notes": "输入0或256时，GaussDB会在\\0处截断",
            "warnings": ["避免对特殊ASCII码使用CHR进行跨库逻辑控制"]
        },
        "LOWER": {
            "notes": "对日期类型的隐式转换结果格式不同",
            "suggestion": "先TO_CHAR格式化日期，再调用大小写转换函数"
        },
        "UPPER": {
            "notes": "对日期类型的隐式转换结果格式不同",
            "suggestion": "先TO_CHAR格式化日期，再调用大小写转换函数"
        },
        "REGEXP_REPLACE": {
            "notes": "参数'n'含义不同；'.'在GaussDB默认匹配换行符，Oracle默认不匹配",
            "suggestion": "检查正则表达式中的'.'，Oracle默认不匹配换行，GaussDB默认匹配"
        },
        "SYSDATE": {
            "target": "SYSDATE",
            "notes": "返回值类型不一致，PL/SQL变量赋值时注意目标变量类型兼容性"
        },
        "NVL": {
            "target": "NVL",  # GaussDB兼容，也可用COALESCE
            "notes": "GaussDB兼容NVL，也支持COALESCE"
        },
        "DECODE": {
            "target": "DECODE",  # GaussDB兼容，也可用CASE WHEN
            "notes": "GaussDB兼容DECODE，也可改用标准CASE WHEN"
        },
    },

    # SQL语法差异
    "sql_syntax": {
        "not_equal_operator": {
            "oracle": "! =",  # 允许空格
            "gaussdb": "!=",  # 禁止空格
            "notes": "'! ='中间有空格时，GaussDB会将'!'识别为阶乘运算",
            "rule": "必须确保!=符号紧凑书写，不能有空格"
        },
        "connect_by": {
            "notes": "GaussDB仅支持CONNECT_BY_FILTERING模式",
            "suggestion": "复杂分层查询建议通过递归CTE (WITH RECURSIVE)改写",
            "example": """
-- Oracle CONNECT BY:
SELECT employee_id, manager_id, LEVEL
FROM employees
START WITH manager_id IS NULL
CONNECT BY PRIOR employee_id = manager_id;

-- GaussDB WITH RECURSIVE:
WITH RECURSIVE emp_hierarchy AS (
    SELECT employee_id, manager_id, 1 AS level
    FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.employee_id, e.manager_id, h.level + 1
    FROM employees e
    JOIN emp_hierarchy h ON e.manager_id = h.employee_id
)
SELECT * FROM emp_hierarchy;
"""
        },
        "rownum": {
            "notes": "在复杂JOIN(Left/Right/Full)条件中使用时过滤时机不同",
            "suggestion": "避免在JOIN ON子句中使用ROWNUM，改在最外层WHERE使用",
            "alternative": "也可使用ROW_NUMBER() OVER() 或 LIMIT"
        },
        "insert_default": {
            "notes": "Oracle必须显式指定列名以匹配子查询，GaussDB可省略并自动补NULL",
            "suggestion": "为兼容性建议始终显式指定列名"
        },
    },

    # PL/SQL差异
    "plsql": {
        "type_attribute": {
            "oracle": "%TYPE",
            "gaussdb": "%TYPE",
            "notes": "不支持record变量的属性引用，不支持多层嵌套引用",
            "warnings": ["避免使用record_var.col%TYPE这种写法"]
        },
        "for_reverse": {
            "notes": "GaussDB要求lower_bound >= upper_bound才会执行",
            "suggestion": "注意循环范围逻辑，Oracle会自动处理范围顺序"
        },
        "collection_compare": {
            "notes": "Oracle忽略成员顺序，GaussDB严格按顺序比较",
            "suggestion": "如果逻辑依赖成员存在性而非顺序，请改用自定义逻辑"
        },
    },

    # 关键改写规则（AI执行迁移时参考）
    "rewrite_rules": [
        {
            "pattern": r"DBMS_LOB\.",
            "replacement": "DBE_LOB.",
            "description": "高级包名替换"
        },
        {
            "pattern": r"DBMS_OUTPUT\.",
            "replacement": "DBE_OUTPUT.",
            "description": "高级包名替换"
        },
        {
            "pattern": r"DBMS_RANDOM\.",
            "replacement": "DBE_RANDOM.",
            "description": "高级包名替换"
        },
        {
            "pattern": r"UTL_RAW\.",
            "replacement": "DBE_RAW.",
            "description": "高级包名替换"
        },
        {
            "pattern": r"DBMS_SQL\.",
            "replacement": "DBE_SQL.",
            "description": "高级包名替换"
        },
        {
            "pattern": r"!\s+=",
            "replacement": "!=",
            "description": "修复不等号空格问题"
        },
        {
            "pattern": r"VARCHAR2\((\d+)\s+CHAR\)",
            "replacement": r"VARCHAR2(\1 * 4)",  # 估算UTF8
            "description": "VARCHAR2 CHAR单位转换"
        },
    ],
}


def get_migration_rules(source_db: str, target_db: str) -> dict:
    """
    Get migration rules for specific database pair

    Args:
        source_db: Source database type (oracle, mysql, postgresql, etc.)
        target_db: Target database type

    Returns:
        Migration rules dictionary
    """
    source_db = source_db.lower()
    target_db = target_db.lower()

    if source_db == "oracle" and target_db == "gaussdb":
        return ORACLE_TO_GAUSSDB_RULES

    # 返回通用规则（其他迁移路径可后续扩展）
    return {
        "description": f"{source_db} to {target_db} migration",
        "version": "1.0",
        "packages": {},
        "data_types": {},
        "functions": {},
        "sql_syntax": {},
        "plsql": {},
        "rewrite_rules": [],
    }


def format_rules_for_prompt(rules: dict, language: str = "zh") -> str:
    """
    Format migration rules for inclusion in AI prompt

    Args:
        rules: Migration rules dictionary
        language: Output language (zh/en)

    Returns:
        Formatted string for prompt
    """
    if not rules or not rules.get("packages"):
        return ""

    lines = []

    if language == "zh":
        lines.append("**Oracle → GaussDB 核心迁移规则：**\n")

        # 高级包
        lines.append("**1. 高级包替换：**")
        lines.append("| Oracle包 | GaussDB包 | 注意事项 |")
        lines.append("|----------|-----------|----------|")
        for pkg, info in rules.get("packages", {}).items():
            notes = info.get("notes", "")[:50]
            lines.append(f"| {pkg} | {info['target']} | {notes} |")

        # 数据类型
        lines.append("\n**2. 数据类型差异：**")
        lines.append("| Oracle类型 | GaussDB处理 | 注意事项 |")
        lines.append("|------------|-------------|----------|")
        for dtype, info in rules.get("data_types", {}).items():
            target = info.get("target", dtype)
            notes = info.get("notes", "")[:40]
            lines.append(f"| {dtype} | {target} | {notes} |")

        # SQL语法
        lines.append("\n**3. SQL语法关键差异：**")
        for key, info in rules.get("sql_syntax", {}).items():
            notes = info.get("notes", "")
            suggestion = info.get("suggestion", "")
            lines.append(f"- **{key}**: {notes}")
            if suggestion:
                lines.append(f"  建议: {suggestion}")

        # PL/SQL
        lines.append("\n**4. PL/SQL差异：**")
        for key, info in rules.get("plsql", {}).items():
            notes = info.get("notes", "")
            lines.append(f"- **{key}**: {notes}")

    else:
        lines.append("**Oracle → GaussDB Core Migration Rules:**\n")

        lines.append("**1. Package Replacements:**")
        lines.append("| Oracle Package | GaussDB Package | Notes |")
        lines.append("|----------------|-----------------|-------|")
        for pkg, info in rules.get("packages", {}).items():
            notes = info.get("notes", "")[:50]
            lines.append(f"| {pkg} | {info['target']} | {notes} |")

        lines.append("\n**2. Data Type Differences:**")
        lines.append("| Oracle Type | GaussDB Handling | Notes |")
        lines.append("|-------------|------------------|-------|")
        for dtype, info in rules.get("data_types", {}).items():
            target = info.get("target", dtype)
            notes = info.get("notes", "")[:40]
            lines.append(f"| {dtype} | {target} | {notes} |")

        lines.append("\n**3. SQL Syntax Key Differences:**")
        for key, info in rules.get("sql_syntax", {}).items():
            notes = info.get("notes", "")
            suggestion = info.get("suggestion", "")
            lines.append(f"- **{key}**: {notes}")
            if suggestion:
                lines.append(f"  Suggestion: {suggestion}")

    return "\n".join(lines)
