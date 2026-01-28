"""
Database Migration Rules - 异构数据库迁移规则
Contains syntax mappings and conversion rules between different databases
"""

# =============================================================================
# Oracle to PostgreSQL Generic Rules (通用规则，也适用于GaussDB作为补充)
# =============================================================================
ORACLE_TO_POSTGRESQL_RULES = {
    "description": "Oracle to PostgreSQL Generic Migration Rules",
    "version": "1.0",
    "notes": "这些规则也适用于GaussDB，作为GaussDB专用规则的补充",

    # 数据类型映射
    "data_types": {
        "NUMBER": {"target": "NUMERIC", "notes": "NUMBER → NUMERIC；NUMBER(n) → NUMERIC(n)；无精度NUMBER → NUMERIC"},
        "NUMBER(1)": {"target": "BOOLEAN", "notes": "可选转换，用于表示布尔值"},
        "NUMBER(3)": {"target": "SMALLINT", "notes": "小整数优化"},
        "NUMBER(10)": {"target": "INTEGER", "notes": "标准整数"},
        "NUMBER(19)": {"target": "BIGINT", "notes": "大整数"},
        "NUMBER(p,s)": {"target": "NUMERIC(p,s)", "notes": "保持精度"},
        "VARCHAR2(n)": {"target": "VARCHAR(n)", "notes": "字符类型"},
        "NVARCHAR2(n)": {"target": "VARCHAR(n)", "notes": "PostgreSQL原生支持Unicode"},
        "CHAR(n)": {"target": "CHAR(n)", "notes": "定长字符"},
        "NCHAR(n)": {"target": "CHAR(n)", "notes": "PostgreSQL原生支持Unicode"},
        "CLOB": {"target": "TEXT", "notes": "大文本"},
        "NCLOB": {"target": "TEXT", "notes": "大文本"},
        "BLOB": {"target": "BYTEA", "notes": "二进制数据"},
        "RAW(n)": {"target": "BYTEA", "notes": "二进制数据"},
        "LONG": {"target": "TEXT", "notes": "已废弃类型"},
        "LONG RAW": {"target": "BYTEA", "notes": "已废弃类型"},
        "DATE": {"target": "TIMESTAMP(0)", "notes": "Oracle DATE包含时间部分"},
        "TIMESTAMP": {"target": "TIMESTAMP", "notes": "时间戳"},
        "TIMESTAMP WITH TIME ZONE": {"target": "TIMESTAMPTZ", "notes": "带时区时间戳"},
        "TIMESTAMP WITH LOCAL TIME ZONE": {"target": "TIMESTAMPTZ", "notes": "转换为带时区"},
        "INTERVAL YEAR TO MONTH": {"target": "INTERVAL", "notes": "间隔类型"},
        "INTERVAL DAY TO SECOND": {"target": "INTERVAL", "notes": "间隔类型"},
        "BINARY_FLOAT": {"target": "REAL", "notes": "单精度浮点"},
        "BINARY_DOUBLE": {"target": "DOUBLE PRECISION", "notes": "双精度浮点"},
        "XMLTYPE": {"target": "XML", "notes": "XML类型"},
        "ROWID": {"target": "CHAR(18)", "notes": "或使用OID"},
        "UROWID": {"target": "VARCHAR(4000)", "notes": "通用ROWID"},
        "BFILE": {"target": "TEXT", "notes": "存储文件路径，文件需外部管理"},
    },

    # 函数映射
    "functions": {
        # 字符串函数
        "CONCAT(a,b)": {"target": "a || b", "notes": "或使用CONCAT函数"},
        "SUBSTR(s,p,l)": {"target": "SUBSTRING(s FROM p FOR l)", "notes": "或SUBSTR兼容"},
        "INSTR(s,sub)": {"target": "POSITION(sub IN s)", "notes": "或STRPOS(s,sub)"},
        "LENGTH(s)": {"target": "LENGTH(s)", "notes": "兼容"},
        "LENGTHB(s)": {"target": "OCTET_LENGTH(s)", "notes": "字节长度"},
        "UPPER(s)": {"target": "UPPER(s)", "notes": "兼容"},
        "LOWER(s)": {"target": "LOWER(s)", "notes": "兼容"},
        "INITCAP(s)": {"target": "INITCAP(s)", "notes": "兼容"},
        "LTRIM(s)": {"target": "LTRIM(s)", "notes": "兼容"},
        "RTRIM(s)": {"target": "RTRIM(s)", "notes": "兼容"},
        "TRIM(s)": {"target": "TRIM(s)", "notes": "兼容"},
        "LPAD(s,n,p)": {"target": "LPAD(s,n,p)", "notes": "兼容"},
        "RPAD(s,n,p)": {"target": "RPAD(s,n,p)", "notes": "兼容"},
        "REPLACE(s,a,b)": {"target": "REPLACE(s,a,b)", "notes": "兼容"},
        "TRANSLATE(s,a,b)": {"target": "TRANSLATE(s,a,b)", "notes": "兼容"},
        "ASCII(s)": {"target": "ASCII(s)", "notes": "兼容"},
        "CHR(n)": {"target": "CHR(n)", "notes": "兼容"},
        "REVERSE(s)": {"target": "REVERSE(s)", "notes": "兼容"},

        # 数值函数
        "ABS(n)": {"target": "ABS(n)", "notes": "兼容"},
        "CEIL(n)": {"target": "CEIL(n)", "notes": "兼容"},
        "FLOOR(n)": {"target": "FLOOR(n)", "notes": "兼容"},
        "ROUND(n,d)": {"target": "ROUND(n,d)", "notes": "兼容"},
        "TRUNC(n,d)": {"target": "TRUNC(n,d)", "notes": "兼容"},
        "MOD(n,m)": {"target": "MOD(n,m)", "notes": "兼容"},
        "POWER(n,m)": {"target": "POWER(n,m)", "notes": "兼容"},
        "SQRT(n)": {"target": "SQRT(n)", "notes": "兼容"},
        "SIGN(n)": {"target": "SIGN(n)", "notes": "兼容"},
        "EXP(n)": {"target": "EXP(n)", "notes": "兼容"},
        "LN(n)": {"target": "LN(n)", "notes": "兼容"},
        "LOG(b,n)": {"target": "LOG(b,n)", "notes": "兼容"},

        # 日期时间函数
        "SYSDATE": {"target": "CURRENT_TIMESTAMP", "notes": "或NOW()或LOCALTIMESTAMP"},
        "SYSTIMESTAMP": {"target": "CURRENT_TIMESTAMP", "notes": "带时区"},
        "CURRENT_DATE": {"target": "CURRENT_DATE", "notes": "兼容"},
        "CURRENT_TIMESTAMP": {"target": "CURRENT_TIMESTAMP", "notes": "兼容"},
        "ADD_MONTHS(d,n)": {"target": "d + INTERVAL 'n months'", "notes": "使用INTERVAL"},
        "MONTHS_BETWEEN(d1,d2)": {"target": "EXTRACT(YEAR FROM AGE(d1,d2))*12 + EXTRACT(MONTH FROM AGE(d1,d2))", "notes": "复杂转换"},
        "LAST_DAY(d)": {"target": "(DATE_TRUNC('MONTH',d) + INTERVAL '1 MONTH - 1 DAY')::DATE", "notes": "需函数或表达式"},
        "NEXT_DAY(d,day)": {"target": "自定义函数", "notes": "需创建函数"},
        "TRUNC(d)": {"target": "DATE_TRUNC('DAY',d)", "notes": "日期截断"},
        "TRUNC(d,'MM')": {"target": "DATE_TRUNC('MONTH',d)", "notes": "月截断"},
        "TRUNC(d,'YY')": {"target": "DATE_TRUNC('YEAR',d)", "notes": "年截断"},
        "EXTRACT(part FROM d)": {"target": "EXTRACT(part FROM d)", "notes": "兼容"},
        "TO_DATE(s,fmt)": {"target": "TO_DATE(s,fmt)", "notes": "格式字符串有差异"},
        "TO_CHAR(d,fmt)": {"target": "TO_CHAR(d,fmt)", "notes": "格式字符串有差异"},
        "TO_TIMESTAMP(s,fmt)": {"target": "TO_TIMESTAMP(s,fmt)", "notes": "格式字符串有差异"},

        # 转换函数
        "TO_NUMBER(s)": {"target": "s::NUMERIC", "notes": "或CAST(s AS NUMERIC)"},
        "TO_CHAR(n)": {"target": "n::TEXT", "notes": "或CAST(n AS TEXT)"},
        "CAST(x AS type)": {"target": "CAST(x AS type)", "notes": "兼容"},
        "HEXTORAW(s)": {"target": "DECODE(s, 'hex')", "notes": "十六进制转换"},
        "RAWTOHEX(r)": {"target": "ENCODE(r, 'hex')", "notes": "转十六进制"},

        # 空值函数
        "NVL(a,b)": {"target": "COALESCE(a,b)", "notes": "标准SQL"},
        "NVL2(a,b,c)": {"target": "CASE WHEN a IS NOT NULL THEN b ELSE c END", "notes": "CASE改写"},
        "NULLIF(a,b)": {"target": "NULLIF(a,b)", "notes": "兼容"},
        "COALESCE(a,b,...)": {"target": "COALESCE(a,b,...)", "notes": "兼容"},
        "DECODE(e,s1,r1,...)": {"target": "CASE e WHEN s1 THEN r1 ... END", "notes": "CASE改写"},
        "CASE WHEN...": {"target": "CASE WHEN...", "notes": "兼容"},

        # 聚合函数
        "COUNT(*)": {"target": "COUNT(*)", "notes": "兼容"},
        "SUM(n)": {"target": "SUM(n)", "notes": "兼容"},
        "AVG(n)": {"target": "AVG(n)", "notes": "兼容"},
        "MIN(n)": {"target": "MIN(n)", "notes": "兼容"},
        "MAX(n)": {"target": "MAX(n)", "notes": "兼容"},
        "LISTAGG(col,sep)": {"target": "STRING_AGG(col,sep)", "notes": "字符串聚合"},
        "WM_CONCAT(col)": {"target": "STRING_AGG(col,',')", "notes": "逗号分隔聚合"},

        # 分析函数
        "ROW_NUMBER() OVER()": {"target": "ROW_NUMBER() OVER()", "notes": "兼容"},
        "RANK() OVER()": {"target": "RANK() OVER()", "notes": "兼容"},
        "DENSE_RANK() OVER()": {"target": "DENSE_RANK() OVER()", "notes": "兼容"},
        "LEAD(col,n) OVER()": {"target": "LEAD(col,n) OVER()", "notes": "兼容"},
        "LAG(col,n) OVER()": {"target": "LAG(col,n) OVER()", "notes": "兼容"},
        "FIRST_VALUE(col) OVER()": {"target": "FIRST_VALUE(col) OVER()", "notes": "兼容"},
        "LAST_VALUE(col) OVER()": {"target": "LAST_VALUE(col) OVER()", "notes": "兼容"},

        # 其他函数
        "ROWNUM": {"target": "ROW_NUMBER() OVER()", "notes": "或LIMIT"},
        "ROWID": {"target": "CTID", "notes": "PostgreSQL行标识"},
        "SYS_GUID()": {"target": "GEN_RANDOM_UUID()", "notes": "或UUID扩展"},
        "USER": {"target": "CURRENT_USER", "notes": "当前用户"},
        "UID": {"target": "自定义", "notes": "需查询系统表"},
        "USERENV('SESSIONID')": {"target": "PG_BACKEND_PID()", "notes": "会话ID"},
        "GREATEST(a,b,...)": {"target": "GREATEST(a,b,...)", "notes": "兼容"},
        "LEAST(a,b,...)": {"target": "LEAST(a,b,...)", "notes": "兼容"},
    },

    # SQL语法差异
    "sql_syntax": {
        # 分页
        "ROWNUM <= n": {
            "target": "LIMIT n",
            "example": "SELECT * FROM t WHERE ROWNUM <= 10 → SELECT * FROM t LIMIT 10"
        },
        "ROWNUM分页": {
            "target": "LIMIT OFFSET",
            "example": """
-- Oracle:
SELECT * FROM (
    SELECT a.*, ROWNUM rn FROM (SELECT * FROM t ORDER BY id) a
    WHERE ROWNUM <= 20
) WHERE rn > 10;

-- PostgreSQL:
SELECT * FROM t ORDER BY id LIMIT 10 OFFSET 10;
"""
        },
        "FETCH FIRST": {
            "target": "LIMIT",
            "example": "FETCH FIRST 10 ROWS ONLY → LIMIT 10"
        },

        # 层次查询
        "CONNECT BY": {
            "target": "WITH RECURSIVE",
            "notes": "递归CTE改写",
            "example": """
-- Oracle:
SELECT id, parent_id, LEVEL FROM t
START WITH parent_id IS NULL
CONNECT BY PRIOR id = parent_id;

-- PostgreSQL:
WITH RECURSIVE cte AS (
    SELECT id, parent_id, 1 AS level FROM t WHERE parent_id IS NULL
    UNION ALL
    SELECT t.id, t.parent_id, cte.level + 1
    FROM t JOIN cte ON t.parent_id = cte.id
)
SELECT * FROM cte;
"""
        },
        "SYS_CONNECT_BY_PATH": {"target": "递归CTE中拼接路径", "notes": "需手动实现"},
        "CONNECT_BY_ROOT": {"target": "递归CTE中保留根节点", "notes": "需手动实现"},
        "LEVEL伪列": {"target": "递归CTE中计数器", "notes": "需手动实现"},

        # 序列
        "seq.NEXTVAL": {"target": "nextval('seq')", "notes": "函数调用"},
        "seq.CURRVAL": {"target": "currval('seq')", "notes": "函数调用"},
        "CREATE SEQUENCE": {
            "target": "CREATE SEQUENCE",
            "notes": "语法略有差异",
            "example": """
-- Oracle:
CREATE SEQUENCE seq START WITH 1 INCREMENT BY 1;

-- PostgreSQL:
CREATE SEQUENCE seq START WITH 1 INCREMENT BY 1;
-- 或使用IDENTITY列:
CREATE TABLE t (id INTEGER GENERATED ALWAYS AS IDENTITY);
"""
        },

        # 外连接
        "(+)外连接": {
            "target": "LEFT/RIGHT JOIN",
            "notes": "标准SQL JOIN语法",
            "example": """
-- Oracle:
SELECT * FROM a, b WHERE a.id = b.id(+);

-- PostgreSQL:
SELECT * FROM a LEFT JOIN b ON a.id = b.id;
"""
        },

        # MERGE语句
        "MERGE INTO": {
            "target": "INSERT ON CONFLICT",
            "notes": "或使用CTE实现UPSERT",
            "example": """
-- Oracle MERGE:
MERGE INTO target t USING source s ON (t.id = s.id)
WHEN MATCHED THEN UPDATE SET t.val = s.val
WHEN NOT MATCHED THEN INSERT (id, val) VALUES (s.id, s.val);

-- PostgreSQL UPSERT:
INSERT INTO target (id, val) SELECT id, val FROM source
ON CONFLICT (id) DO UPDATE SET val = EXCLUDED.val;
"""
        },

        # 空字符串
        "空字符串处理": {
            "notes": "Oracle中''等同于NULL，PostgreSQL中''是空字符串",
            "warning": "这是重要差异，需检查业务逻辑"
        },

        # 引号
        "标识符引号": {
            "notes": "Oracle不区分大小写（除非用双引号），PostgreSQL小写存储",
            "suggestion": "统一使用小写标识符或一致使用双引号"
        },

        # 别名
        "列别名AS": {
            "notes": "Oracle可省略AS，PostgreSQL建议显式使用AS"
        },

        # 删除
        "DELETE无FROM": {
            "target": "DELETE FROM",
            "example": "DELETE t WHERE id=1 → DELETE FROM t WHERE id=1"
        },
    },

    # PL/SQL到PL/pgSQL转换
    "plsql_to_plpgsql": {
        "过程声明": {
            "oracle": "CREATE OR REPLACE PROCEDURE proc_name AS",
            "postgresql": "CREATE OR REPLACE PROCEDURE proc_name() LANGUAGE plpgsql AS $$",
        },
        "函数声明": {
            "oracle": "CREATE OR REPLACE FUNCTION func_name RETURN type AS",
            "postgresql": "CREATE OR REPLACE FUNCTION func_name() RETURNS type LANGUAGE plpgsql AS $$",
        },
        "变量声明": {
            "notes": "DECLARE块位置不同，PostgreSQL在$$和BEGIN之间"
        },
        "游标FOR循环": {
            "notes": "语法基本兼容"
        },
        "异常处理": {
            "oracle": "EXCEPTION WHEN exception_name THEN",
            "postgresql": "EXCEPTION WHEN exception_name THEN",
            "notes": "异常名称不同，如NO_DATA_FOUND在PG中可能需要检查FOUND变量"
        },
        "动态SQL": {
            "oracle": "EXECUTE IMMEDIATE sql_string",
            "postgresql": "EXECUTE sql_string",
        },
        "包(PACKAGE)": {
            "notes": "PostgreSQL无PACKAGE概念，改用SCHEMA组织函数或扩展"
        },
        "触发器": {
            "notes": "语法差异较大，需单独转换"
        },
    },

    # 系统表/视图映射
    "system_objects": {
        "DUAL": {"target": "无需FROM或FROM(SELECT 1)", "notes": "SELECT 1+1 无需FROM"},
        "USER_TABLES": {"target": "information_schema.tables", "notes": "或pg_tables"},
        "USER_TAB_COLUMNS": {"target": "information_schema.columns", "notes": "或pg_attribute"},
        "USER_INDEXES": {"target": "pg_indexes", "notes": "系统视图"},
        "USER_CONSTRAINTS": {"target": "information_schema.table_constraints", "notes": "约束信息"},
        "USER_SEQUENCES": {"target": "information_schema.sequences", "notes": "序列信息"},
        "ALL_*": {"target": "information_schema.*或pg_catalog.*", "notes": "全部对象"},
        "DBA_*": {"target": "pg_catalog.*", "notes": "需超级用户"},
        "V$SESSION": {"target": "pg_stat_activity", "notes": "会话信息"},
        "V$SQL": {"target": "pg_stat_statements", "notes": "需扩展"},
        "V$LOCK": {"target": "pg_locks", "notes": "锁信息"},
    },
}


# =============================================================================
# Oracle to GaussDB Specific Rules (GaussDB专用规则)
# =============================================================================
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

    if source_db == "oracle" and target_db == "postgresql":
        return ORACLE_TO_POSTGRESQL_RULES

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


def get_combined_oracle_to_gaussdb_rules() -> dict:
    """
    Get combined Oracle to GaussDB rules (GaussDB specific + PostgreSQL generic)

    Returns:
        Combined rules dictionary with GaussDB specific rules taking precedence
    """
    return {
        "gaussdb_specific": ORACLE_TO_GAUSSDB_RULES,
        "postgresql_generic": ORACLE_TO_POSTGRESQL_RULES,
        "notes": "GaussDB专用规则优先，核心规则之外的不兼容项参考PostgreSQL通用规则"
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
