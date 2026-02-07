"""
Migration Handler - Extracted migration-related methods from SQLTuningAgent.
"""
import json
import logging
from typing import Dict, List, Any, TYPE_CHECKING

from db_agent.i18n import t
from .database import DatabaseToolsFactory
from db_agent.storage.models import MigrationTask, MigrationItem

if TYPE_CHECKING:
    from db_agent.storage import SQLiteStorage

logger = logging.getLogger(__name__)


class MigrationHandler:
    """Handles all database migration operations."""

    def __init__(self, storage: "SQLiteStorage", db_tools, db_type: str):
        self.storage = storage
        self.db_tools = db_tools
        self.db_type = db_type

    def analyze_source_database(self, source_connection_name: str,
                                schema: str = None,
                                object_types: List[str] = None,
                                **kwargs) -> Dict[str, Any]:
        """Analyze source database for migration"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        # Get source connection
        source_conn = self.storage.get_connection(source_connection_name)
        if not source_conn:
            return {"status": "error", "error": t("migration_source_not_found", name=source_connection_name)}

        try:
            # Decrypt password and create source db tools
            from db_agent.storage.encryption import decrypt
            password = decrypt(source_conn.password_encrypted)
            source_config = {
                "type": source_conn.db_type,
                "host": source_conn.host,
                "port": source_conn.port,
                "database": source_conn.database,
                "user": source_conn.username,
                "password": password
            }
            source_tools = DatabaseToolsFactory.create(source_conn.db_type, source_config)

            # Get all objects
            objects_result = source_tools.get_all_objects(schema=schema, object_types=object_types)
            if objects_result.get("status") == "error":
                return objects_result

            # Get FK dependencies for table ordering
            fk_deps = source_tools.get_foreign_key_dependencies(schema=schema)

            # Get object dependencies
            obj_deps = source_tools.get_object_dependencies(schema=schema)

            return {
                "status": "success",
                "source_connection": source_connection_name,
                "source_db_type": source_conn.db_type,
                "schema": schema or objects_result.get("schema"),
                "objects": objects_result.get("objects", {}),
                "total_count": objects_result.get("total_count", 0),
                "table_order": fk_deps.get("table_order", []) if fk_deps.get("status") == "success" else [],
                "foreign_keys": fk_deps.get("foreign_keys", []) if fk_deps.get("status") == "success" else [],
                "dependencies": obj_deps.get("dependencies", []) if obj_deps.get("status") == "success" else []
            }

        except Exception as e:
            logger.error(f"Failed to analyze source database: {e}")
            return {"status": "error", "error": str(e)}

    def create_migration_plan(self, task_id: int,
                              source_connection_name: str,
                              target_schema: str = None,
                              **kwargs) -> Dict[str, Any]:
        """Create migration plan with converted DDL"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        # Get task
        task = self.storage.get_migration_task(task_id)
        if not task:
            return {"status": "error", "error": t("migration_task_not_found", id=task_id)}

        # Get source connection
        source_conn = self.storage.get_connection(source_connection_name)
        if not source_conn:
            return {"status": "error", "error": t("migration_source_not_found", name=source_connection_name)}

        try:
            # Create source db tools
            from db_agent.storage.encryption import decrypt
            password = decrypt(source_conn.password_encrypted)
            source_config = {
                "type": source_conn.db_type,
                "host": source_conn.host,
                "port": source_conn.port,
                "database": source_conn.database,
                "user": source_conn.username,
                "password": password
            }
            source_tools = DatabaseToolsFactory.create(source_conn.db_type, source_config)

            # Get objects and dependencies
            objects_result = source_tools.get_all_objects(schema=task.source_schema)
            fk_deps = source_tools.get_foreign_key_dependencies(schema=task.source_schema)

            if objects_result.get("status") == "error":
                return objects_result

            objects = objects_result.get("objects", {})
            table_order = fk_deps.get("table_order", []) if fk_deps.get("status") == "success" else []

            # Build migration items
            items = []
            execution_order = 0

            # 1. Sequences first
            for seq in objects.get("sequences", []):
                execution_order += 1
                ddl_result = source_tools.get_object_ddl("sequence", seq["name"], task.source_schema)
                items.append(MigrationItem(
                    id=None,
                    task_id=task_id,
                    object_type="sequence",
                    object_name=seq["name"],
                    schema_name=task.source_schema,
                    execution_order=execution_order,
                    depends_on=None,
                    status="pending",
                    source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                    target_ddl=None,  # Will be converted later
                    conversion_notes=None,
                    execution_result=None,
                    error_message=None,
                    retry_count=0,
                    executed_at=None,
                    created_at=None,
                    updated_at=None
                ))

            # 2. Tables in dependency order
            tables_added = set()
            for table_name in table_order:
                if table_name not in tables_added:
                    execution_order += 1
                    ddl_result = source_tools.get_object_ddl("table", table_name, task.source_schema)
                    deps = ddl_result.get("dependencies", []) if ddl_result.get("status") == "success" else []
                    items.append(MigrationItem(
                        id=None,
                        task_id=task_id,
                        object_type="table",
                        object_name=table_name,
                        schema_name=task.source_schema,
                        execution_order=execution_order,
                        depends_on=json.dumps([d["name"] for d in deps]) if deps else None,
                        status="pending",
                        source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                        target_ddl=None,
                        conversion_notes=None,
                        execution_result=None,
                        error_message=None,
                        retry_count=0,
                        executed_at=None,
                        created_at=None,
                        updated_at=None
                    ))
                    tables_added.add(table_name)

            # Add remaining tables not in FK dependency list
            for table in objects.get("tables", []):
                if table["name"] not in tables_added:
                    execution_order += 1
                    ddl_result = source_tools.get_object_ddl("table", table["name"], task.source_schema)
                    items.append(MigrationItem(
                        id=None,
                        task_id=task_id,
                        object_type="table",
                        object_name=table["name"],
                        schema_name=task.source_schema,
                        execution_order=execution_order,
                        depends_on=None,
                        status="pending",
                        source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                        target_ddl=None,
                        conversion_notes=None,
                        execution_result=None,
                        error_message=None,
                        retry_count=0,
                        executed_at=None,
                        created_at=None,
                        updated_at=None
                    ))

            # 3. Indexes (excluding primary keys which are created with tables)
            for idx in objects.get("indexes", []):
                if not idx.get("is_primary"):
                    execution_order += 1
                    ddl_result = source_tools.get_object_ddl("index", idx["name"], task.source_schema)
                    items.append(MigrationItem(
                        id=None,
                        task_id=task_id,
                        object_type="index",
                        object_name=idx["name"],
                        schema_name=task.source_schema,
                        execution_order=execution_order,
                        depends_on=json.dumps([idx.get("table_name")]) if idx.get("table_name") else None,
                        status="pending",
                        source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                        target_ddl=None,
                        conversion_notes=None,
                        execution_result=None,
                        error_message=None,
                        retry_count=0,
                        executed_at=None,
                        created_at=None,
                        updated_at=None
                    ))

            # 4. Views
            for view in objects.get("views", []):
                execution_order += 1
                ddl_result = source_tools.get_object_ddl("view", view["name"], task.source_schema)
                items.append(MigrationItem(
                    id=None,
                    task_id=task_id,
                    object_type="view",
                    object_name=view["name"],
                    schema_name=task.source_schema,
                    execution_order=execution_order,
                    depends_on=None,
                    status="pending",
                    source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                    target_ddl=None,
                    conversion_notes=None,
                    execution_result=None,
                    error_message=None,
                    retry_count=0,
                    executed_at=None,
                    created_at=None,
                    updated_at=None
                ))

            # 5. Functions
            for func in objects.get("functions", []):
                execution_order += 1
                ddl_result = source_tools.get_object_ddl("function", func["name"], task.source_schema)
                items.append(MigrationItem(
                    id=None,
                    task_id=task_id,
                    object_type="function",
                    object_name=func["name"],
                    schema_name=task.source_schema,
                    execution_order=execution_order,
                    depends_on=None,
                    status="pending",
                    source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                    target_ddl=None,
                    conversion_notes=None,
                    execution_result=None,
                    error_message=None,
                    retry_count=0,
                    executed_at=None,
                    created_at=None,
                    updated_at=None
                ))

            # 6. Procedures
            for proc in objects.get("procedures", []):
                execution_order += 1
                ddl_result = source_tools.get_object_ddl("procedure", proc["name"], task.source_schema)
                items.append(MigrationItem(
                    id=None,
                    task_id=task_id,
                    object_type="procedure",
                    object_name=proc["name"],
                    schema_name=task.source_schema,
                    execution_order=execution_order,
                    depends_on=None,
                    status="pending",
                    source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                    target_ddl=None,
                    conversion_notes=None,
                    execution_result=None,
                    error_message=None,
                    retry_count=0,
                    executed_at=None,
                    created_at=None,
                    updated_at=None
                ))

            # 7. Triggers
            for trigger in objects.get("triggers", []):
                execution_order += 1
                ddl_result = source_tools.get_object_ddl("trigger", trigger["name"], task.source_schema)
                items.append(MigrationItem(
                    id=None,
                    task_id=task_id,
                    object_type="trigger",
                    object_name=trigger["name"],
                    schema_name=task.source_schema,
                    execution_order=execution_order,
                    depends_on=json.dumps([trigger.get("table_name")]) if trigger.get("table_name") else None,
                    status="pending",
                    source_ddl=ddl_result.get("ddl") if ddl_result.get("status") == "success" else None,
                    target_ddl=None,
                    conversion_notes=None,
                    execution_result=None,
                    error_message=None,
                    retry_count=0,
                    executed_at=None,
                    created_at=None,
                    updated_at=None
                ))

            # Save items to database
            if items:
                self.storage.add_migration_items_batch(items)

            # Update task
            self.storage.update_migration_task_status(task_id, "planning")
            self.storage.update_migration_task_analysis(
                task_id,
                json.dumps({"objects": {k: len(v) for k, v in objects.items()}}),
                len(items)
            )

            return {
                "status": "success",
                "task_id": task_id,
                "total_items": len(items),
                "items_by_type": {
                    "sequences": len([i for i in items if i.object_type == "sequence"]),
                    "tables": len([i for i in items if i.object_type == "table"]),
                    "indexes": len([i for i in items if i.object_type == "index"]),
                    "views": len([i for i in items if i.object_type == "view"]),
                    "functions": len([i for i in items if i.object_type == "function"]),
                    "procedures": len([i for i in items if i.object_type == "procedure"]),
                    "triggers": len([i for i in items if i.object_type == "trigger"])
                }
            }

        except Exception as e:
            logger.error(f"Failed to create migration plan: {e}")
            return {"status": "error", "error": str(e)}

    def get_migration_plan(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Get migration plan details"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        task = self.storage.get_migration_task(task_id)
        if not task:
            return {"status": "error", "error": t("migration_task_not_found", id=task_id)}

        items = self.storage.get_migration_items(task_id)

        return {
            "status": "success",
            "task": task.to_dict(),
            "items": [item.to_dict() for item in items],
            "summary": {
                "total": len(items),
                "pending": len([i for i in items if i.status == "pending"]),
                "completed": len([i for i in items if i.status == "completed"]),
                "failed": len([i for i in items if i.status == "failed"]),
                "skipped": len([i for i in items if i.status == "skipped"])
            }
        }

    def get_migration_status(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Get migration status summary"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        summary = self.storage.get_migration_summary(task_id)
        if not summary:
            return {"status": "error", "error": t("migration_task_not_found", id=task_id)}

        return {"status": "success", **summary}

    def convert_ddl(self, source_ddl: str, source_type: str, target_type: str, object_type: str) -> Dict[str, Any]:
        """
        Convert DDL from source database type to target database type.
        Returns dict with 'ddl' and 'notes' keys.
        """
        if not source_ddl:
            return {"ddl": None, "notes": "No source DDL"}

        if source_type == target_type:
            return {"ddl": source_ddl, "notes": "Same database type, no conversion needed"}

        ddl = source_ddl
        notes = []

        # MySQL to PostgreSQL conversion
        if source_type == "mysql" and target_type == "postgresql":
            import re

            # Data type conversions
            type_mappings = [
                (r'\bINT\s+AUTO_INCREMENT\b', 'SERIAL', 'INT AUTO_INCREMENT -> SERIAL'),
                (r'\bBIGINT\s+AUTO_INCREMENT\b', 'BIGSERIAL', 'BIGINT AUTO_INCREMENT -> BIGSERIAL'),
                (r'\bSMALLINT\s+AUTO_INCREMENT\b', 'SMALLSERIAL', 'SMALLINT AUTO_INCREMENT -> SMALLSERIAL'),
                (r'\bINT\b(?!\s*\()', 'INTEGER', 'INT -> INTEGER'),
                (r'\bTINYINT\s*\(\s*1\s*\)', 'BOOLEAN', 'TINYINT(1) -> BOOLEAN'),
                (r'\bTINYINT\b', 'SMALLINT', 'TINYINT -> SMALLINT'),
                (r'\bMEDIUMINT\b', 'INTEGER', 'MEDIUMINT -> INTEGER'),
                (r'\bDOUBLE\b(?!\s+PRECISION)', 'DOUBLE PRECISION', 'DOUBLE -> DOUBLE PRECISION'),
                (r'\bFLOAT\b', 'REAL', 'FLOAT -> REAL'),
                (r'\bDATETIME\b', 'TIMESTAMP', 'DATETIME -> TIMESTAMP'),
                (r'\bTIMESTAMP\s+DEFAULT\s+CURRENT_TIMESTAMP\s+ON\s+UPDATE\s+CURRENT_TIMESTAMP\b',
                 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 'Removed ON UPDATE (use trigger in PG)'),
                (r'\bLONGTEXT\b', 'TEXT', 'LONGTEXT -> TEXT'),
                (r'\bMEDIUMTEXT\b', 'TEXT', 'MEDIUMTEXT -> TEXT'),
                (r'\bTINYTEXT\b', 'TEXT', 'TINYTEXT -> TEXT'),
                (r'\bLONGBLOB\b', 'BYTEA', 'LONGBLOB -> BYTEA'),
                (r'\bMEDIUMBLOB\b', 'BYTEA', 'MEDIUMBLOB -> BYTEA'),
                (r'\bTINYBLOB\b', 'BYTEA', 'TINYBLOB -> BYTEA'),
                (r'\bBLOB\b', 'BYTEA', 'BLOB -> BYTEA'),
                (r'\bVARBINARY\s*\([^)]+\)', 'BYTEA', 'VARBINARY -> BYTEA'),
                (r'\bBINARY\s*\([^)]+\)', 'BYTEA', 'BINARY -> BYTEA'),
                (r'\bJSON\b', 'JSONB', 'JSON -> JSONB'),
            ]

            for pattern, replacement, note in type_mappings:
                if re.search(pattern, ddl, re.IGNORECASE):
                    ddl = re.sub(pattern, replacement, ddl, flags=re.IGNORECASE)
                    notes.append(note)

            # Remove MySQL-specific clauses
            mysql_clauses = [
                (r'\s+ENGINE\s*=\s*\w+', '', 'Removed ENGINE clause'),
                (r'\s+DEFAULT\s+CHARSET\s*=\s*\w+', '', 'Removed CHARSET clause'),
                (r'\s+COLLATE\s*=?\s*\w+', '', 'Removed COLLATE clause'),
                (r'\s+AUTO_INCREMENT\s*=\s*\d+', '', 'Removed AUTO_INCREMENT value'),
                (r'\s+ROW_FORMAT\s*=\s*\w+', '', 'Removed ROW_FORMAT'),
                (r'\s+COMMENT\s*=?\s*\'[^\']*\'', '', 'Removed table COMMENT'),
                (r'\s+UNSIGNED\b', '', 'Removed UNSIGNED (not in PostgreSQL)'),
                (r'\s+ZEROFILL\b', '', 'Removed ZEROFILL'),
                (r'\bIF\s+NOT\s+EXISTS\s+', '', 'Removed IF NOT EXISTS'),
            ]

            for pattern, replacement, note in mysql_clauses:
                if re.search(pattern, ddl, re.IGNORECASE):
                    ddl = re.sub(pattern, replacement, ddl, flags=re.IGNORECASE)
                    notes.append(note)

            # Handle ENUM - convert to VARCHAR with CHECK constraint (simplified)
            enum_pattern = r"ENUM\s*\(([^)]+)\)"
            if re.search(enum_pattern, ddl, re.IGNORECASE):
                ddl = re.sub(enum_pattern, "VARCHAR(50)", ddl, flags=re.IGNORECASE)
                notes.append("ENUM -> VARCHAR(50) (consider adding CHECK constraint)")

            # Handle column comments - remove inline COMMENT
            ddl = re.sub(r"\s+COMMENT\s+'[^']*'", "", ddl, flags=re.IGNORECASE)

            # Handle GENERATED columns (MySQL syntax differs)
            ddl = re.sub(r'\s+GENERATED\s+ALWAYS\s+AS\s+\(([^)]+)\)\s+STORED',
                        r' GENERATED ALWAYS AS (\1) STORED', ddl, flags=re.IGNORECASE)

            # Handle index syntax differences for CREATE INDEX
            if object_type == "index":
                # Remove USING BTREE if present (BTREE is default in PG)
                ddl = re.sub(r'\s+USING\s+BTREE\b', '', ddl, flags=re.IGNORECASE)
                # Handle USING HASH
                if re.search(r'\bUSING\s+HASH\b', ddl, re.IGNORECASE):
                    notes.append("HASH index may behave differently in PostgreSQL")

            # Handle FULLTEXT indexes - not directly supported in PG
            if 'FULLTEXT' in ddl.upper():
                notes.append("FULLTEXT index not supported - consider using GIN/GiST with tsvector")
                return {"ddl": None, "notes": "; ".join(notes), "skip_reason": "FULLTEXT index not supported in PostgreSQL"}

        # MySQL to GaussDB (similar to PostgreSQL with some differences)
        elif source_type == "mysql" and target_type == "gaussdb":
            # GaussDB is PostgreSQL-compatible, use same rules
            result = self.convert_ddl(source_ddl, "mysql", "postgresql", object_type)
            result["notes"] = result.get("notes", "") + " (GaussDB compatibility mode)"
            return result

        # Oracle to PostgreSQL
        elif source_type == "oracle" and target_type == "postgresql":
            import re

            type_mappings = [
                (r'\bNUMBER\s*\(\s*10\s*\)', 'INTEGER', 'NUMBER(10) -> INTEGER'),
                (r'\bNUMBER\s*\(\s*19\s*\)', 'BIGINT', 'NUMBER(19) -> BIGINT'),
                (r'\bNUMBER\s*\((\d+)\s*,\s*(\d+)\s*\)', r'NUMERIC(\1,\2)', 'NUMBER(p,s) -> NUMERIC(p,s)'),
                (r'\bNUMBER\b', 'NUMERIC', 'NUMBER -> NUMERIC'),
                (r'\bVARCHAR2\s*\((\d+)\)', r'VARCHAR(\1)', 'VARCHAR2 -> VARCHAR'),
                (r'\bNVARCHAR2\s*\((\d+)\)', r'VARCHAR(\1)', 'NVARCHAR2 -> VARCHAR'),
                (r'\bCLOB\b', 'TEXT', 'CLOB -> TEXT'),
                (r'\bNCLOB\b', 'TEXT', 'NCLOB -> TEXT'),
                (r'\bBLOB\b', 'BYTEA', 'BLOB -> BYTEA'),
                (r'\bRAW\s*\(\d+\)', 'BYTEA', 'RAW -> BYTEA'),
                (r'\bSYSDATE\b', 'CURRENT_TIMESTAMP', 'SYSDATE -> CURRENT_TIMESTAMP'),
                (r'\bSYSTIMESTAMP\b', 'CURRENT_TIMESTAMP', 'SYSTIMESTAMP -> CURRENT_TIMESTAMP'),
            ]

            for pattern, replacement, note in type_mappings:
                if re.search(pattern, ddl, re.IGNORECASE):
                    ddl = re.sub(pattern, replacement, ddl, flags=re.IGNORECASE)
                    notes.append(note)

        # Other conversions can be added here...

        return {"ddl": ddl.strip(), "notes": "; ".join(notes) if notes else "Basic conversion applied"}

    def execute_migration_item(self, item_id: int, **kwargs) -> Dict[str, Any]:
        """Execute a single migration item"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        item = self.storage.get_migration_item(item_id)
        if not item:
            return {"status": "error", "error": t("migration_item_not_found", id=item_id)}

        # Get task to know source/target types
        task = self.storage.get_migration_task(item.task_id)
        if not task:
            return {"status": "error", "error": t("migration_task_not_found", task_id=item.task_id)}

        # Update item status to executing
        self.storage.update_migration_item_status(item_id, "executing")

        try:
            # Convert DDL if needed
            if item.target_ddl:
                ddl = item.target_ddl
            elif item.source_ddl:
                # Convert source DDL to target format
                conversion = self.convert_ddl(
                    item.source_ddl,
                    task.source_db_type,
                    task.target_db_type,
                    item.object_type
                )

                if conversion.get("skip_reason"):
                    # Item should be skipped
                    self.storage.update_migration_item_status(
                        item_id, "skipped",
                        conversion.get("skip_reason")
                    )
                    # Save conversion notes
                    if conversion.get("notes"):
                        self.storage.update_migration_item_ddl(
                            item_id,
                            conversion_notes=conversion.get("notes")
                        )
                    if task:
                        self.storage.update_migration_task_progress(
                            item.task_id,
                            skipped=task.skipped_items + 1
                        )
                    return {
                        "status": "skipped",
                        "item_id": item_id,
                        "object_type": item.object_type,
                        "object_name": item.object_name,
                        "reason": conversion.get("skip_reason"),
                        "notes": conversion.get("notes")
                    }

                ddl = conversion.get("ddl")
                if conversion.get("notes"):
                    self.storage.update_migration_item_ddl(
                        item_id,
                        target_ddl=ddl,
                        conversion_notes=conversion.get("notes")
                    )
            else:
                ddl = None

            if not ddl:
                self.storage.update_migration_item_status(item_id, "failed", "No DDL available")
                return {"status": "error", "error": "No DDL available for this item"}

            # Execute DDL on target database
            result = self.db_tools.execute_sql(ddl, confirmed=True)

            if result.get("status") == "success":
                self.storage.update_migration_item_status(
                    item_id, "completed",
                    execution_result=json.dumps(result)
                )

                # Update task progress
                task = self.storage.get_migration_task(item.task_id)
                if task:
                    self.storage.update_migration_task_progress(
                        item.task_id,
                        completed=task.completed_items + 1
                    )

                return {
                    "status": "success",
                    "item_id": item_id,
                    "object_type": item.object_type,
                    "object_name": item.object_name,
                    "result": result
                }
            else:
                error_msg = result.get("error", "Unknown error")
                self.storage.update_migration_item_status(item_id, "failed", error_msg)

                # Update task progress
                task = self.storage.get_migration_task(item.task_id)
                if task:
                    self.storage.update_migration_task_progress(
                        item.task_id,
                        failed=task.failed_items + 1
                    )

                return {
                    "status": "error",
                    "item_id": item_id,
                    "object_type": item.object_type,
                    "object_name": item.object_name,
                    "error": error_msg
                }

        except Exception as e:
            error_msg = str(e)
            self.storage.update_migration_item_status(item_id, "failed", error_msg)
            return {"status": "error", "error": error_msg}

    def execute_migration_batch(self, task_id: int, batch_size: int = 10, **kwargs) -> Dict[str, Any]:
        """Execute migration items in batch"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        results = []
        completed = 0
        failed = 0

        # Update task status to executing
        self.storage.update_migration_task_status(task_id, "executing")

        for _ in range(batch_size):
            item = self.storage.get_next_pending_item(task_id)
            if not item:
                break

            result = self.execute_migration_item(item.id)
            results.append({
                "item_id": item.id,
                "object_type": item.object_type,
                "object_name": item.object_name,
                "status": result.get("status")
            })

            if result.get("status") == "success":
                completed += 1
            else:
                failed += 1

        # Check if all items are done
        summary = self.storage.get_migration_summary(task_id)
        if summary and summary.get("status_counts", {}).get("pending", 0) == 0:
            final_status = "completed" if summary.get("failed_items", 0) == 0 else "completed"
            self.storage.update_migration_task_status(task_id, final_status)

        return {
            "status": "success",
            "task_id": task_id,
            "batch_completed": completed,
            "batch_failed": failed,
            "results": results
        }

    def compare_databases(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Compare source and target databases"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        task = self.storage.get_migration_task(task_id)
        if not task:
            return {"status": "error", "error": t("migration_task_not_found", id=task_id)}

        try:
            # Get source connection
            source_conn = self.storage.get_connection_by_id(task.source_connection_id)
            target_conn = self.storage.get_connection_by_id(task.target_connection_id)

            if not source_conn or not target_conn:
                return {"status": "error", "error": "Connection not found"}

            # Create source tools
            from db_agent.storage.encryption import decrypt
            source_password = decrypt(source_conn.password_encrypted)
            source_config = {
                "type": source_conn.db_type,
                "host": source_conn.host,
                "port": source_conn.port,
                "database": source_conn.database,
                "user": source_conn.username,
                "password": source_password
            }
            source_tools = DatabaseToolsFactory.create(source_conn.db_type, source_config)

            # Get objects from both databases
            source_objects = source_tools.get_all_objects(schema=task.source_schema)
            target_objects = self.db_tools.get_all_objects(schema=task.target_schema)

            # Compare
            comparison = {"matches": [], "missing_in_target": [], "extra_in_target": []}

            source_tables = {t["name"] for t in source_objects.get("objects", {}).get("tables", [])}
            target_tables = {t["name"] for t in target_objects.get("objects", {}).get("tables", [])}

            comparison["matches"] = list(source_tables & target_tables)
            comparison["missing_in_target"] = list(source_tables - target_tables)
            comparison["extra_in_target"] = list(target_tables - source_tables)

            return {
                "status": "success",
                "task_id": task_id,
                "source_db": source_conn.db_type,
                "target_db": target_conn.db_type,
                "comparison": comparison,
                "summary": {
                    "total_source_tables": len(source_tables),
                    "total_target_tables": len(target_tables),
                    "matched": len(comparison["matches"]),
                    "missing": len(comparison["missing_in_target"]),
                    "extra": len(comparison["extra_in_target"])
                }
            }

        except Exception as e:
            logger.error(f"Failed to compare databases: {e}")
            return {"status": "error", "error": str(e)}

    def generate_migration_report(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Generate migration report"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        task = self.storage.get_migration_task(task_id)
        if not task:
            return {"status": "error", "error": t("migration_task_not_found", id=task_id)}

        items = self.storage.get_migration_items(task_id)
        summary = self.storage.get_migration_summary(task_id)

        # Group items by status
        items_by_status = {
            "pending": [],
            "completed": [],
            "failed": [],
            "skipped": []
        }
        for item in items:
            if item.status in items_by_status:
                items_by_status[item.status].append({
                    "id": item.id,
                    "type": item.object_type,
                    "name": item.object_name,
                    "error": item.error_message
                })

        report = {
            "status": "success",
            "task_id": task_id,
            "task_name": task.name,
            "source_db_type": task.source_db_type,
            "target_db_type": task.target_db_type,
            "task_status": task.status,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "statistics": {
                "total_items": task.total_items,
                "completed": task.completed_items,
                "failed": task.failed_items,
                "skipped": task.skipped_items,
                "pending": task.total_items - task.completed_items - task.failed_items - task.skipped_items
            },
            "items_by_type": summary.get("type_counts", {}) if summary else {},
            "failed_items": items_by_status["failed"],
            "skipped_items": items_by_status["skipped"]
        }

        return report

    def skip_migration_item(self, item_id: int, reason: str = None, **kwargs) -> Dict[str, Any]:
        """Skip a migration item"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        item = self.storage.get_migration_item(item_id)
        if not item:
            return {"status": "error", "error": t("migration_item_not_found", id=item_id)}

        self.storage.update_migration_item_status(item_id, "skipped", reason)

        # Update task progress
        task = self.storage.get_migration_task(item.task_id)
        if task:
            self.storage.update_migration_task_progress(
                item.task_id,
                skipped=task.skipped_items + 1
            )

        return {
            "status": "success",
            "item_id": item_id,
            "object_type": item.object_type,
            "object_name": item.object_name,
            "reason": reason
        }

    def retry_failed_items(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Retry all failed migration items"""
        if not self.storage:
            return {"status": "error", "error": t("migration_storage_required")}

        failed_items = self.storage.get_migration_items(task_id, status="failed")
        if not failed_items:
            return {"status": "success", "message": "No failed items to retry", "retried": 0}

        retried = 0
        for item in failed_items:
            self.storage.increment_migration_item_retry(item.id)
            retried += 1

        # Reset task failed count
        task = self.storage.get_migration_task(task_id)
        if task:
            self.storage.update_migration_task_progress(task_id, failed=0)
            self.storage.update_migration_task_status(task_id, "executing")

        return {
            "status": "success",
            "task_id": task_id,
            "retried": retried
        }


class SkillExecutorHelper:
    """Helper for executing skills, requiring skill_registry and session_id."""

    def __init__(self, skill_registry: "SkillRegistry", session_id: int = None):
        self.skill_registry = skill_registry
        self.session_id = session_id

    def execute_skill(self, skill_name: str, arguments: str = "") -> Dict[str, Any]:
        """
        Execute a Skill tool call.

        Args:
            skill_name: Skill name
            arguments: Arguments to pass to the Skill

        Returns:
            Result dictionary
        """
        if not self.skill_registry:
            return {
                "status": "error",
                "error": "Skill registry not initialized"
            }

        skill = self.skill_registry.get(skill_name)
        if not skill:
            return {
                "status": "error",
                "error": f"Skill not found: {skill_name}"
            }

        # Import executor here to avoid circular imports
        from db_agent.skills import SkillExecutor

        executor = SkillExecutor(self.skill_registry, session_id=str(self.session_id) if self.session_id else None)
        result = executor.execute_skill(skill, arguments)

        if result.get("status") == "success":
            # Return the processed instructions for the AI to follow
            return {
                "status": "success",
                "skill_name": skill_name,
                "instructions": result.get("instructions", ""),
                "source": "skill"
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "Unknown skill error"),
                "source": "skill"
            }
