"""
SQLite storage for persistent configuration data
"""
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from .models import DatabaseConnection, LLMProvider, Preference, Session, ChatMessage, MigrationTask, MigrationItem, MCPServer, AuditLog
from .encryption import encrypt, decrypt


class SQLiteStorage:
    """SQLite-based storage for database connections and LLM providers"""

    DEFAULT_DB_PATH = os.path.join(str(Path.home()), '.db-agent', 'data.db')

    def __init__(self, db_path: str = None):
        """
        Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file. Defaults to ~/.db-agent/data.db
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH

        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, mode=0o700)

        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Initialize database tables"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Database connections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS database_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    db_type TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    db_name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password_encrypted TEXT NOT NULL,
                    is_active INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # LLM providers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS llm_providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    provider TEXT NOT NULL,
                    api_key_encrypted TEXT NOT NULL,
                    model TEXT NOT NULL,
                    base_url TEXT,
                    is_default INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    connection_id INTEGER,
                    provider_id INTEGER,
                    is_current INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (connection_id) REFERENCES database_connections(id) ON DELETE SET NULL,
                    FOREIGN KEY (provider_id) REFERENCES llm_providers(id) ON DELETE SET NULL
                )
            ''')

            # Chat messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    tool_calls TEXT,
                    tool_call_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            ''')

            # Context summaries table for storing compressed conversation summaries
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS context_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    summary_text TEXT NOT NULL,
                    messages_summarized_count INTEGER,
                    original_token_count INTEGER,
                    compressed_token_count INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            ''')

            # Migration tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS migration_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    source_connection_id INTEGER NOT NULL,
                    target_connection_id INTEGER NOT NULL,
                    source_db_type TEXT NOT NULL,
                    target_db_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    total_items INTEGER DEFAULT 0,
                    completed_items INTEGER DEFAULT 0,
                    failed_items INTEGER DEFAULT 0,
                    skipped_items INTEGER DEFAULT 0,
                    source_schema TEXT,
                    target_schema TEXT,
                    options TEXT,
                    analysis_result TEXT,
                    error_message TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_connection_id) REFERENCES database_connections(id),
                    FOREIGN KEY (target_connection_id) REFERENCES database_connections(id)
                )
            ''')

            # Migration items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS migration_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    object_type TEXT NOT NULL,
                    object_name TEXT NOT NULL,
                    schema_name TEXT,
                    execution_order INTEGER NOT NULL,
                    depends_on TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    source_ddl TEXT,
                    target_ddl TEXT,
                    conversion_notes TEXT,
                    execution_result TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    executed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES migration_tasks(id) ON DELETE CASCADE
                )
            ''')

            # MCP servers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mcp_servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    command TEXT NOT NULL,
                    args TEXT NOT NULL DEFAULT '[]',
                    env TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Audit logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    connection_id INTEGER,
                    category TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target_type TEXT,
                    target_name TEXT,
                    sql_text TEXT,
                    parameters TEXT,
                    result_status TEXT NOT NULL,
                    result_summary TEXT,
                    affected_rows INTEGER,
                    execution_time_ms INTEGER,
                    user_confirmed INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
                    FOREIGN KEY (connection_id) REFERENCES database_connections(id) ON DELETE SET NULL
                )
            ''')

            # Indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id
                ON chat_messages(session_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_is_current
                ON sessions(is_current)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_context_summaries_session_id
                ON context_summaries(session_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_migration_tasks_status
                ON migration_tasks(status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_migration_items_task_id
                ON migration_items(task_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_migration_items_status
                ON migration_items(status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_mcp_servers_enabled
                ON mcp_servers(enabled)
            ''')

            # Audit logs indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_audit_logs_session
                ON audit_logs(session_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_audit_logs_category
                ON audit_logs(category)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
                ON audit_logs(created_at)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_audit_logs_action
                ON audit_logs(action)
            ''')

            conn.commit()
        finally:
            conn.close()

    # ==================== Database Connection Methods ====================

    def add_connection(self, conn: DatabaseConnection) -> int:
        """
        Add a new database connection.

        Args:
            conn: DatabaseConnection object (id field is ignored)

        Returns:
            The ID of the newly created connection
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO database_connections
                (name, db_type, host, port, db_name, username, password_encrypted, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                conn.name,
                conn.db_type,
                conn.host,
                conn.port,
                conn.database,
                conn.username,
                conn.password_encrypted,
                1 if conn.is_active else 0,
                now,
                now
            ))

            db_conn.commit()
            return cursor.lastrowid
        finally:
            db_conn.close()

    def get_connection(self, name: str) -> Optional[DatabaseConnection]:
        """
        Get a database connection by name.

        Args:
            name: Connection name

        Returns:
            DatabaseConnection object or None if not found
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM database_connections WHERE name = ?',
                (name,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_connection(row)
            return None
        finally:
            db_conn.close()

    def get_connection_by_id(self, conn_id: int) -> Optional[DatabaseConnection]:
        """Get a database connection by ID."""
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM database_connections WHERE id = ?',
                (conn_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_connection(row)
            return None
        finally:
            db_conn.close()

    def get_active_connection(self) -> Optional[DatabaseConnection]:
        """
        Get the currently active database connection.

        Returns:
            DatabaseConnection object or None if no active connection
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM database_connections WHERE is_active = 1 LIMIT 1'
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_connection(row)
            return None
        finally:
            db_conn.close()

    def list_connections(self) -> List[DatabaseConnection]:
        """
        List all database connections.

        Returns:
            List of DatabaseConnection objects
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute('SELECT * FROM database_connections ORDER BY name')
            rows = cursor.fetchall()
            return [self._row_to_connection(row) for row in rows]
        finally:
            db_conn.close()

    def update_connection(self, conn: DatabaseConnection) -> bool:
        """
        Update an existing database connection.

        Args:
            conn: DatabaseConnection object with updated values

        Returns:
            True if update was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                UPDATE database_connections
                SET db_type = ?, host = ?, port = ?, db_name = ?,
                    username = ?, password_encrypted = ?, is_active = ?, updated_at = ?
                WHERE name = ?
            ''', (
                conn.db_type,
                conn.host,
                conn.port,
                conn.database,
                conn.username,
                conn.password_encrypted,
                1 if conn.is_active else 0,
                now,
                conn.name
            ))

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def delete_connection(self, name: str) -> bool:
        """
        Delete a database connection.

        Args:
            name: Connection name

        Returns:
            True if deletion was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'DELETE FROM database_connections WHERE name = ?',
                (name,)
            )
            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def set_active_connection(self, name: str) -> bool:
        """
        Set a connection as the active connection.

        Args:
            name: Connection name to set as active

        Returns:
            True if successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            # Deactivate all connections
            cursor.execute(
                'UPDATE database_connections SET is_active = 0, updated_at = ?',
                (now,)
            )

            # Activate the specified connection
            cursor.execute(
                'UPDATE database_connections SET is_active = 1, updated_at = ? WHERE name = ?',
                (now, name)
            )

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def _row_to_connection(self, row: sqlite3.Row) -> DatabaseConnection:
        """Convert a database row to DatabaseConnection object"""
        return DatabaseConnection(
            id=row['id'],
            name=row['name'],
            db_type=row['db_type'],
            host=row['host'],
            port=row['port'],
            database=row['db_name'],
            username=row['username'],
            password_encrypted=row['password_encrypted'],
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    # ==================== LLM Provider Methods ====================

    def add_provider(self, provider: LLMProvider) -> int:
        """
        Add a new LLM provider.

        Args:
            provider: LLMProvider object (id field is ignored)

        Returns:
            The ID of the newly created provider
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO llm_providers
                (name, provider, api_key_encrypted, model, base_url, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                provider.name,
                provider.provider,
                provider.api_key_encrypted,
                provider.model,
                provider.base_url,
                1 if provider.is_default else 0,
                now,
                now
            ))

            db_conn.commit()
            return cursor.lastrowid
        finally:
            db_conn.close()

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """
        Get an LLM provider by name.

        Args:
            name: Provider name

        Returns:
            LLMProvider object or None if not found
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM llm_providers WHERE name = ?',
                (name,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_provider(row)
            return None
        finally:
            db_conn.close()

    def get_provider_by_id(self, provider_id: int) -> Optional[LLMProvider]:
        """Get an LLM provider by ID."""
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM llm_providers WHERE id = ?',
                (provider_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_provider(row)
            return None
        finally:
            db_conn.close()

    def get_default_provider(self) -> Optional[LLMProvider]:
        """
        Get the default LLM provider.

        Returns:
            LLMProvider object or None if no default provider
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM llm_providers WHERE is_default = 1 LIMIT 1'
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_provider(row)
            return None
        finally:
            db_conn.close()

    def list_providers(self) -> List[LLMProvider]:
        """
        List all LLM providers.

        Returns:
            List of LLMProvider objects
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute('SELECT * FROM llm_providers ORDER BY name')
            rows = cursor.fetchall()
            return [self._row_to_provider(row) for row in rows]
        finally:
            db_conn.close()

    def update_provider(self, provider: LLMProvider) -> bool:
        """
        Update an existing LLM provider.

        Args:
            provider: LLMProvider object with updated values

        Returns:
            True if update was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                UPDATE llm_providers
                SET provider = ?, api_key_encrypted = ?, model = ?,
                    base_url = ?, is_default = ?, updated_at = ?
                WHERE name = ?
            ''', (
                provider.provider,
                provider.api_key_encrypted,
                provider.model,
                provider.base_url,
                1 if provider.is_default else 0,
                now,
                provider.name
            ))

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def delete_provider(self, name: str) -> bool:
        """
        Delete an LLM provider.

        Args:
            name: Provider name

        Returns:
            True if deletion was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'DELETE FROM llm_providers WHERE name = ?',
                (name,)
            )
            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def set_default_provider(self, name: str) -> bool:
        """
        Set a provider as the default provider.

        Args:
            name: Provider name to set as default

        Returns:
            True if successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            # Remove default flag from all providers
            cursor.execute(
                'UPDATE llm_providers SET is_default = 0, updated_at = ?',
                (now,)
            )

            # Set the specified provider as default
            cursor.execute(
                'UPDATE llm_providers SET is_default = 1, updated_at = ? WHERE name = ?',
                (now, name)
            )

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def _row_to_provider(self, row: sqlite3.Row) -> LLMProvider:
        """Convert a database row to LLMProvider object"""
        return LLMProvider(
            id=row['id'],
            name=row['name'],
            provider=row['provider'],
            api_key_encrypted=row['api_key_encrypted'],
            model=row['model'],
            base_url=row['base_url'],
            is_default=bool(row['is_default']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    # ==================== Preference Methods ====================

    def get_preference(self, key: str) -> Optional[str]:
        """
        Get a preference value.

        Args:
            key: Preference key

        Returns:
            Preference value or None if not found
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT value FROM preferences WHERE key = ?',
                (key,)
            )
            row = cursor.fetchone()
            if row:
                return row['value']
            return None
        finally:
            db_conn.close()

    def set_preference(self, key: str, value: str) -> bool:
        """
        Set a preference value.

        Args:
            key: Preference key
            value: Preference value

        Returns:
            True if successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT OR REPLACE INTO preferences (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, now))

            db_conn.commit()
            return True
        finally:
            db_conn.close()

    def delete_preference(self, key: str) -> bool:
        """
        Delete a preference.

        Args:
            key: Preference key

        Returns:
            True if deletion was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'DELETE FROM preferences WHERE key = ?',
                (key,)
            )
            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    # ==================== Utility Methods ====================

    def has_any_configuration(self) -> bool:
        """
        Check if there is any configuration stored.

        Returns:
            True if there are any connections or providers
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM database_connections')
            conn_count = cursor.fetchone()['count']

            cursor.execute('SELECT COUNT(*) as count FROM llm_providers')
            provider_count = cursor.fetchone()['count']

            return conn_count > 0 and provider_count > 0
        finally:
            db_conn.close()

    def clear_all_data(self):
        """Clear all data from storage (for testing purposes)"""
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute('DELETE FROM database_connections')
            cursor.execute('DELETE FROM llm_providers')
            cursor.execute('DELETE FROM preferences')
            cursor.execute('DELETE FROM chat_messages')
            cursor.execute('DELETE FROM sessions')
            db_conn.commit()
        finally:
            db_conn.close()

    # ==================== Session Methods ====================

    def create_session(self, name: str, connection_id: int = None, provider_id: int = None) -> int:
        """
        Create a new session.

        Args:
            name: Session name
            connection_id: Associated database connection ID
            provider_id: Associated LLM provider ID

        Returns:
            The ID of the newly created session
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO sessions
                (name, connection_id, provider_id, is_current, created_at, updated_at)
                VALUES (?, ?, ?, 0, ?, ?)
            ''', (name, connection_id, provider_id, now, now))

            db_conn.commit()
            return cursor.lastrowid
        finally:
            db_conn.close()

    def get_session(self, session_id: int) -> Optional[Session]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session object or None if not found
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM sessions WHERE id = ?',
                (session_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_session(row)
            return None
        finally:
            db_conn.close()

    def get_session_by_name(self, name: str) -> Optional[Session]:
        """
        Get a session by name.

        Args:
            name: Session name

        Returns:
            Session object or None if not found
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM sessions WHERE name = ?',
                (name,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_session(row)
            return None
        finally:
            db_conn.close()

    def get_current_session(self) -> Optional[Session]:
        """
        Get the current active session.

        Returns:
            Session object or None if no current session
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM sessions WHERE is_current = 1 LIMIT 1'
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_session(row)
            return None
        finally:
            db_conn.close()

    def list_sessions(self, limit: int = 50) -> List[Session]:
        """
        List all sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of Session objects
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?',
                (limit,)
            )
            rows = cursor.fetchall()
            return [self._row_to_session(row) for row in rows]
        finally:
            db_conn.close()

    def delete_session(self, session_id: int) -> bool:
        """
        Delete a session and its messages (CASCADE).

        Args:
            session_id: Session ID

        Returns:
            True if deletion was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            # First delete messages (in case CASCADE doesn't work)
            cursor.execute(
                'DELETE FROM chat_messages WHERE session_id = ?',
                (session_id,)
            )
            # Then delete session
            cursor.execute(
                'DELETE FROM sessions WHERE id = ?',
                (session_id,)
            )
            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def set_current_session(self, session_id: int) -> bool:
        """
        Set a session as the current session.

        Args:
            session_id: Session ID to set as current

        Returns:
            True if successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            # Remove current flag from all sessions
            cursor.execute(
                'UPDATE sessions SET is_current = 0, updated_at = ?',
                (now,)
            )

            # Set the specified session as current
            cursor.execute(
                'UPDATE sessions SET is_current = 1, updated_at = ? WHERE id = ?',
                (now, session_id)
            )

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def rename_session(self, session_id: int, new_name: str) -> bool:
        """
        Rename a session.

        Args:
            session_id: Session ID
            new_name: New session name

        Returns:
            True if successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute(
                'UPDATE sessions SET name = ?, updated_at = ? WHERE id = ?',
                (new_name, now, session_id)
            )

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def update_session_timestamp(self, session_id: int) -> bool:
        """
        Update the session's updated_at timestamp.

        Args:
            session_id: Session ID

        Returns:
            True if successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute(
                'UPDATE sessions SET updated_at = ? WHERE id = ?',
                (now, session_id)
            )

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        """Convert a database row to Session object"""
        return Session(
            id=row['id'],
            name=row['name'],
            connection_id=row['connection_id'],
            provider_id=row['provider_id'],
            is_current=bool(row['is_current']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    # ==================== Chat Message Methods ====================

    def add_message(self, session_id: int, role: str, content: str = None,
                    tool_calls: str = None, tool_call_id: str = None) -> int:
        """
        Add a chat message to a session.

        Args:
            session_id: Session ID
            role: Message role ("user", "assistant", "tool")
            content: Message content
            tool_calls: JSON formatted tool calls (for assistant messages)
            tool_call_id: Tool call ID (for tool messages)

        Returns:
            The ID of the newly created message
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO chat_messages
                (session_id, role, content, tool_calls, tool_call_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, role, content, tool_calls, tool_call_id, now))

            # Update session timestamp
            cursor.execute(
                'UPDATE sessions SET updated_at = ? WHERE id = ?',
                (now, session_id)
            )

            db_conn.commit()
            return cursor.lastrowid
        finally:
            db_conn.close()

    def get_session_messages(self, session_id: int) -> List[ChatMessage]:
        """
        Get all messages for a session.

        Args:
            session_id: Session ID

        Returns:
            List of ChatMessage objects ordered by creation time
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC',
                (session_id,)
            )
            rows = cursor.fetchall()
            return [self._row_to_message(row) for row in rows]
        finally:
            db_conn.close()

    def get_session_message_count(self, session_id: int) -> int:
        """
        Get the number of messages in a session.

        Args:
            session_id: Session ID

        Returns:
            Number of messages
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) as count FROM chat_messages WHERE session_id = ?',
                (session_id,)
            )
            row = cursor.fetchone()
            return row['count'] if row else 0
        finally:
            db_conn.close()

    def clear_session_messages(self, session_id: int) -> bool:
        """
        Clear all messages from a session.

        Args:
            session_id: Session ID

        Returns:
            True if successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'DELETE FROM chat_messages WHERE session_id = ?',
                (session_id,)
            )
            db_conn.commit()
            return True
        finally:
            db_conn.close()

    def _row_to_message(self, row: sqlite3.Row) -> ChatMessage:
        """Convert a database row to ChatMessage object"""
        return ChatMessage(
            id=row['id'],
            session_id=row['session_id'],
            role=row['role'],
            content=row['content'],
            tool_calls=row['tool_calls'],
            tool_call_id=row['tool_call_id'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )

    # ==================== Context Summary Methods ====================

    def save_context_summary(
        self,
        session_id: int,
        summary_text: str,
        messages_count: int,
        original_tokens: int,
        compressed_tokens: int
    ) -> int:
        """
        Save a context compression summary.

        Args:
            session_id: Session ID
            summary_text: The compressed summary text
            messages_count: Number of messages that were summarized
            original_tokens: Original token count before compression
            compressed_tokens: Token count after compression

        Returns:
            The ID of the newly created summary record
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO context_summaries
                (session_id, summary_text, messages_summarized_count,
                 original_token_count, compressed_token_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, summary_text, messages_count, original_tokens, compressed_tokens, now))

            db_conn.commit()
            return cursor.lastrowid
        finally:
            db_conn.close()

    def get_latest_context_summary(self, session_id: int) -> Optional[Dict]:
        """
        Get the latest context summary for a session.

        Args:
            session_id: Session ID

        Returns:
            Dictionary with summary info or None if not found
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute('''
                SELECT * FROM context_summaries
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (session_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'session_id': row['session_id'],
                    'summary_text': row['summary_text'],
                    'messages_summarized_count': row['messages_summarized_count'],
                    'original_token_count': row['original_token_count'],
                    'compressed_token_count': row['compressed_token_count'],
                    'created_at': datetime.fromisoformat(row['created_at']) if row['created_at'] else None
                }
            return None
        finally:
            db_conn.close()

    def get_context_summaries(self, session_id: int) -> List[Dict]:
        """
        Get all context summaries for a session.

        Args:
            session_id: Session ID

        Returns:
            List of summary dictionaries
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute('''
                SELECT * FROM context_summaries
                WHERE session_id = ?
                ORDER BY created_at ASC
            ''', (session_id,))
            rows = cursor.fetchall()
            return [{
                'id': row['id'],
                'session_id': row['session_id'],
                'summary_text': row['summary_text'],
                'messages_summarized_count': row['messages_summarized_count'],
                'original_token_count': row['original_token_count'],
                'compressed_token_count': row['compressed_token_count'],
                'created_at': datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            } for row in rows]
        finally:
            db_conn.close()

    def delete_oldest_messages(self, session_id: int, count: int) -> bool:
        """
        Delete the oldest N messages from a session.

        Args:
            session_id: Session ID
            count: Number of oldest messages to delete

        Returns:
            True if successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()

            # Get the IDs of the oldest N messages
            cursor.execute('''
                SELECT id FROM chat_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
            ''', (session_id, count))
            rows = cursor.fetchall()

            if rows:
                ids_to_delete = [row['id'] for row in rows]
                placeholders = ','.join('?' * len(ids_to_delete))
                cursor.execute(
                    f'DELETE FROM chat_messages WHERE id IN ({placeholders})',
                    ids_to_delete
                )
                db_conn.commit()
                return cursor.rowcount > 0

            return False
        finally:
            db_conn.close()

    # ==================== Migration Task Methods ====================

    def create_migration_task(self, task: MigrationTask) -> int:
        """
        Create a new migration task.

        Args:
            task: MigrationTask object (id field is ignored)

        Returns:
            The ID of the newly created task
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO migration_tasks
                (name, source_connection_id, target_connection_id, source_db_type, target_db_type,
                 status, total_items, completed_items, failed_items, skipped_items,
                 source_schema, target_schema, options, analysis_result, error_message,
                 started_at, completed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.name,
                task.source_connection_id,
                task.target_connection_id,
                task.source_db_type,
                task.target_db_type,
                task.status,
                task.total_items,
                task.completed_items,
                task.failed_items,
                task.skipped_items,
                task.source_schema,
                task.target_schema,
                task.options,
                task.analysis_result,
                task.error_message,
                task.started_at.isoformat() if task.started_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
                now,
                now
            ))

            db_conn.commit()
            return cursor.lastrowid
        finally:
            db_conn.close()

    def get_migration_task(self, task_id: int) -> Optional[MigrationTask]:
        """
        Get a migration task by ID.

        Args:
            task_id: Task ID

        Returns:
            MigrationTask object or None if not found
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM migration_tasks WHERE id = ?',
                (task_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_migration_task(row)
            return None
        finally:
            db_conn.close()

    def list_migration_tasks(self, status: str = None, limit: int = 50) -> List[MigrationTask]:
        """
        List migration tasks.

        Args:
            status: Filter by status (optional)
            limit: Maximum number of tasks to return

        Returns:
            List of MigrationTask objects
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            if status:
                cursor.execute(
                    'SELECT * FROM migration_tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?',
                    (status, limit)
                )
            else:
                cursor.execute(
                    'SELECT * FROM migration_tasks ORDER BY created_at DESC LIMIT ?',
                    (limit,)
                )
            rows = cursor.fetchall()
            return [self._row_to_migration_task(row) for row in rows]
        finally:
            db_conn.close()

    def update_migration_task_status(self, task_id: int, status: str, error_message: str = None) -> bool:
        """
        Update migration task status.

        Args:
            task_id: Task ID
            status: New status
            error_message: Error message (optional)

        Returns:
            True if update was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            if status == 'executing' and error_message is None:
                cursor.execute(
                    'UPDATE migration_tasks SET status = ?, started_at = ?, updated_at = ? WHERE id = ?',
                    (status, now, now, task_id)
                )
            elif status in ('completed', 'failed'):
                cursor.execute(
                    'UPDATE migration_tasks SET status = ?, error_message = ?, completed_at = ?, updated_at = ? WHERE id = ?',
                    (status, error_message, now, now, task_id)
                )
            else:
                cursor.execute(
                    'UPDATE migration_tasks SET status = ?, error_message = ?, updated_at = ? WHERE id = ?',
                    (status, error_message, now, task_id)
                )

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def update_migration_task_progress(self, task_id: int, completed: int = None,
                                        failed: int = None, skipped: int = None) -> bool:
        """
        Update migration task progress counters.

        Args:
            task_id: Task ID
            completed: New completed count (optional)
            failed: New failed count (optional)
            skipped: New skipped count (optional)

        Returns:
            True if update was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            updates = ['updated_at = ?']
            params = [now]

            if completed is not None:
                updates.append('completed_items = ?')
                params.append(completed)
            if failed is not None:
                updates.append('failed_items = ?')
                params.append(failed)
            if skipped is not None:
                updates.append('skipped_items = ?')
                params.append(skipped)

            params.append(task_id)
            cursor.execute(
                f'UPDATE migration_tasks SET {", ".join(updates)} WHERE id = ?',
                params
            )

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def update_migration_task_analysis(self, task_id: int, analysis_result: str, total_items: int) -> bool:
        """
        Update migration task analysis result.

        Args:
            task_id: Task ID
            analysis_result: JSON analysis result
            total_items: Total number of items to migrate

        Returns:
            True if update was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute(
                'UPDATE migration_tasks SET analysis_result = ?, total_items = ?, updated_at = ? WHERE id = ?',
                (analysis_result, total_items, now, task_id)
            )

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def delete_migration_task(self, task_id: int) -> bool:
        """
        Delete a migration task and all its items (CASCADE).

        Args:
            task_id: Task ID

        Returns:
            True if deletion was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            # First delete items (in case CASCADE doesn't work)
            cursor.execute(
                'DELETE FROM migration_items WHERE task_id = ?',
                (task_id,)
            )
            # Then delete task
            cursor.execute(
                'DELETE FROM migration_tasks WHERE id = ?',
                (task_id,)
            )
            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def _row_to_migration_task(self, row: sqlite3.Row) -> MigrationTask:
        """Convert a database row to MigrationTask object"""
        return MigrationTask(
            id=row['id'],
            name=row['name'],
            source_connection_id=row['source_connection_id'],
            target_connection_id=row['target_connection_id'],
            source_db_type=row['source_db_type'],
            target_db_type=row['target_db_type'],
            status=row['status'],
            total_items=row['total_items'],
            completed_items=row['completed_items'],
            failed_items=row['failed_items'],
            skipped_items=row['skipped_items'],
            source_schema=row['source_schema'],
            target_schema=row['target_schema'],
            options=row['options'],
            analysis_result=row['analysis_result'],
            error_message=row['error_message'],
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    # ==================== Migration Item Methods ====================

    def add_migration_item(self, item: MigrationItem) -> int:
        """
        Add a migration item.

        Args:
            item: MigrationItem object (id field is ignored)

        Returns:
            The ID of the newly created item
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO migration_items
                (task_id, object_type, object_name, schema_name, execution_order,
                 depends_on, status, source_ddl, target_ddl, conversion_notes,
                 execution_result, error_message, retry_count, executed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.task_id,
                item.object_type,
                item.object_name,
                item.schema_name,
                item.execution_order,
                item.depends_on,
                item.status,
                item.source_ddl,
                item.target_ddl,
                item.conversion_notes,
                item.execution_result,
                item.error_message,
                item.retry_count,
                item.executed_at.isoformat() if item.executed_at else None,
                now,
                now
            ))

            db_conn.commit()
            return cursor.lastrowid
        finally:
            db_conn.close()

    def add_migration_items_batch(self, items: List[MigrationItem]) -> List[int]:
        """
        Add multiple migration items in a batch.

        Args:
            items: List of MigrationItem objects

        Returns:
            List of IDs of the newly created items
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()
            ids = []

            for item in items:
                cursor.execute('''
                    INSERT INTO migration_items
                    (task_id, object_type, object_name, schema_name, execution_order,
                     depends_on, status, source_ddl, target_ddl, conversion_notes,
                     execution_result, error_message, retry_count, executed_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.task_id,
                    item.object_type,
                    item.object_name,
                    item.schema_name,
                    item.execution_order,
                    item.depends_on,
                    item.status,
                    item.source_ddl,
                    item.target_ddl,
                    item.conversion_notes,
                    item.execution_result,
                    item.error_message,
                    item.retry_count,
                    item.executed_at.isoformat() if item.executed_at else None,
                    now,
                    now
                ))
                ids.append(cursor.lastrowid)

            db_conn.commit()
            return ids
        finally:
            db_conn.close()

    def get_migration_items(self, task_id: int, status: str = None) -> List[MigrationItem]:
        """
        Get migration items for a task.

        Args:
            task_id: Task ID
            status: Filter by status (optional)

        Returns:
            List of MigrationItem objects ordered by execution_order
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            if status:
                cursor.execute(
                    'SELECT * FROM migration_items WHERE task_id = ? AND status = ? ORDER BY execution_order',
                    (task_id, status)
                )
            else:
                cursor.execute(
                    'SELECT * FROM migration_items WHERE task_id = ? ORDER BY execution_order',
                    (task_id,)
                )
            rows = cursor.fetchall()
            return [self._row_to_migration_item(row) for row in rows]
        finally:
            db_conn.close()

    def get_migration_item(self, item_id: int) -> Optional[MigrationItem]:
        """
        Get a migration item by ID.

        Args:
            item_id: Item ID

        Returns:
            MigrationItem object or None if not found
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM migration_items WHERE id = ?',
                (item_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_migration_item(row)
            return None
        finally:
            db_conn.close()

    def get_next_pending_item(self, task_id: int) -> Optional[MigrationItem]:
        """
        Get the next pending item for a task.

        Args:
            task_id: Task ID

        Returns:
            Next pending MigrationItem or None if none pending
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM migration_items WHERE task_id = ? AND status = ? ORDER BY execution_order LIMIT 1',
                (task_id, 'pending')
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_migration_item(row)
            return None
        finally:
            db_conn.close()

    def update_migration_item_status(self, item_id: int, status: str,
                                      error_message: str = None, execution_result: str = None) -> bool:
        """
        Update migration item status.

        Args:
            item_id: Item ID
            status: New status
            error_message: Error message (optional)
            execution_result: JSON execution result (optional)

        Returns:
            True if update was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            if status in ('completed', 'failed', 'skipped'):
                cursor.execute('''
                    UPDATE migration_items
                    SET status = ?, error_message = ?, execution_result = ?, executed_at = ?, updated_at = ?
                    WHERE id = ?
                ''', (status, error_message, execution_result, now, now, item_id))
            else:
                cursor.execute(
                    'UPDATE migration_items SET status = ?, error_message = ?, updated_at = ? WHERE id = ?',
                    (status, error_message, now, item_id)
                )

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def update_migration_item_ddl(self, item_id: int, source_ddl: str = None,
                                   target_ddl: str = None, conversion_notes: str = None) -> bool:
        """
        Update migration item DDL.

        Args:
            item_id: Item ID
            source_ddl: Source DDL (optional)
            target_ddl: Target DDL (optional)
            conversion_notes: JSON conversion notes (optional)

        Returns:
            True if update was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            updates = ['updated_at = ?']
            params = [now]

            if source_ddl is not None:
                updates.append('source_ddl = ?')
                params.append(source_ddl)
            if target_ddl is not None:
                updates.append('target_ddl = ?')
                params.append(target_ddl)
            if conversion_notes is not None:
                updates.append('conversion_notes = ?')
                params.append(conversion_notes)

            params.append(item_id)
            cursor.execute(
                f'UPDATE migration_items SET {", ".join(updates)} WHERE id = ?',
                params
            )

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def increment_migration_item_retry(self, item_id: int) -> bool:
        """
        Increment the retry count for a migration item and reset status to pending.

        Args:
            item_id: Item ID

        Returns:
            True if update was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                UPDATE migration_items
                SET retry_count = retry_count + 1, status = 'pending', error_message = NULL, updated_at = ?
                WHERE id = ?
            ''', (now, item_id))

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def get_migration_summary(self, task_id: int) -> Dict:
        """
        Get a summary of migration progress.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with progress statistics
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()

            # Get task info
            cursor.execute('SELECT * FROM migration_tasks WHERE id = ?', (task_id,))
            task_row = cursor.fetchone()
            if not task_row:
                return {}

            # Get item counts by status
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM migration_items
                WHERE task_id = ?
                GROUP BY status
            ''', (task_id,))
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

            # Get item counts by object type
            cursor.execute('''
                SELECT object_type, COUNT(*) as count
                FROM migration_items
                WHERE task_id = ?
                GROUP BY object_type
            ''', (task_id,))
            type_counts = {row['object_type']: row['count'] for row in cursor.fetchall()}

            # Get failed items
            cursor.execute('''
                SELECT id, object_type, object_name, error_message
                FROM migration_items
                WHERE task_id = ? AND status = 'failed'
                ORDER BY execution_order
            ''', (task_id,))
            failed_items = [{
                'id': row['id'],
                'object_type': row['object_type'],
                'object_name': row['object_name'],
                'error_message': row['error_message']
            } for row in cursor.fetchall()]

            return {
                'task_id': task_id,
                'task_name': task_row['name'],
                'status': task_row['status'],
                'source_db_type': task_row['source_db_type'],
                'target_db_type': task_row['target_db_type'],
                'total_items': task_row['total_items'],
                'completed_items': task_row['completed_items'],
                'failed_items': task_row['failed_items'],
                'skipped_items': task_row['skipped_items'],
                'status_counts': status_counts,
                'type_counts': type_counts,
                'failed_item_details': failed_items,
                'started_at': task_row['started_at'],
                'completed_at': task_row['completed_at']
            }
        finally:
            db_conn.close()

    def _row_to_migration_item(self, row: sqlite3.Row) -> MigrationItem:
        """Convert a database row to MigrationItem object"""
        return MigrationItem(
            id=row['id'],
            task_id=row['task_id'],
            object_type=row['object_type'],
            object_name=row['object_name'],
            schema_name=row['schema_name'],
            execution_order=row['execution_order'],
            depends_on=row['depends_on'],
            status=row['status'],
            source_ddl=row['source_ddl'],
            target_ddl=row['target_ddl'],
            conversion_notes=row['conversion_notes'],
            execution_result=row['execution_result'],
            error_message=row['error_message'],
            retry_count=row['retry_count'],
            executed_at=datetime.fromisoformat(row['executed_at']) if row['executed_at'] else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    # ==================== MCP Server Methods ====================

    def add_mcp_server(self, server: MCPServer) -> int:
        """
        Add a new MCP server configuration.

        Args:
            server: MCPServer object (id field is ignored)

        Returns:
            The ID of the newly created server config
        """
        import json as _json
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO mcp_servers
                (name, command, args, env, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                server.name,
                server.command,
                server.args if isinstance(server.args, str) else _json.dumps(server.args),
                server.env if isinstance(server.env, str) or server.env is None else _json.dumps(server.env),
                1 if server.enabled else 0,
                now,
                now
            ))

            db_conn.commit()
            return cursor.lastrowid
        finally:
            db_conn.close()

    def get_mcp_server(self, name: str) -> Optional[MCPServer]:
        """
        Get an MCP server configuration by name.

        Args:
            name: Server name

        Returns:
            MCPServer object or None if not found
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM mcp_servers WHERE name = ?',
                (name,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_mcp_server(row)
            return None
        finally:
            db_conn.close()

    def get_mcp_server_by_id(self, server_id: int) -> Optional[MCPServer]:
        """Get an MCP server configuration by ID."""
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM mcp_servers WHERE id = ?',
                (server_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_mcp_server(row)
            return None
        finally:
            db_conn.close()

    def list_mcp_servers(self, enabled_only: bool = False) -> List[Dict]:
        """
        List all MCP server configurations.

        Args:
            enabled_only: If True, only return enabled servers

        Returns:
            List of server configuration dictionaries
        """
        import json as _json
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            if enabled_only:
                cursor.execute('SELECT * FROM mcp_servers WHERE enabled = 1 ORDER BY name')
            else:
                cursor.execute('SELECT * FROM mcp_servers ORDER BY name')
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    'id': row['id'],
                    'name': row['name'],
                    'command': row['command'],
                    'args': _json.loads(row['args']) if row['args'] else [],
                    'env': _json.loads(row['env']) if row['env'] else None,
                    'enabled': bool(row['enabled']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            return result
        finally:
            db_conn.close()

    def update_mcp_server(self, server: MCPServer) -> bool:
        """
        Update an existing MCP server configuration.

        Args:
            server: MCPServer object with updated values

        Returns:
            True if update was successful
        """
        import json as _json
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                UPDATE mcp_servers
                SET command = ?, args = ?, env = ?, enabled = ?, updated_at = ?
                WHERE name = ?
            ''', (
                server.command,
                server.args if isinstance(server.args, str) else _json.dumps(server.args),
                server.env if isinstance(server.env, str) or server.env is None else _json.dumps(server.env),
                1 if server.enabled else 0,
                now,
                server.name
            ))

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def delete_mcp_server(self, name: str) -> bool:
        """
        Delete an MCP server configuration.

        Args:
            name: Server name

        Returns:
            True if deletion was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'DELETE FROM mcp_servers WHERE name = ?',
                (name,)
            )
            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def enable_mcp_server(self, name: str, enabled: bool = True) -> bool:
        """
        Enable or disable an MCP server.

        Args:
            name: Server name
            enabled: Whether to enable (True) or disable (False)

        Returns:
            True if update was successful
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute(
                'UPDATE mcp_servers SET enabled = ?, updated_at = ? WHERE name = ?',
                (1 if enabled else 0, now, name)
            )

            db_conn.commit()
            return cursor.rowcount > 0
        finally:
            db_conn.close()

    def _row_to_mcp_server(self, row: sqlite3.Row) -> MCPServer:
        """Convert a database row to MCPServer object"""
        return MCPServer(
            id=row['id'],
            name=row['name'],
            command=row['command'],
            args=row['args'],
            env=row['env'],
            enabled=bool(row['enabled']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    # ==================== Audit Log Methods ====================

    def add_audit_log(self, log: AuditLog) -> int:
        """
        Add a new audit log entry.

        Args:
            log: AuditLog object (id field is ignored)

        Returns:
            The ID of the newly created audit log
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO audit_logs
                (session_id, connection_id, category, action, target_type, target_name,
                 sql_text, parameters, result_status, result_summary, affected_rows,
                 execution_time_ms, user_confirmed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log.session_id,
                log.connection_id,
                log.category,
                log.action,
                log.target_type,
                log.target_name,
                log.sql_text,
                log.parameters,
                log.result_status,
                log.result_summary,
                log.affected_rows,
                log.execution_time_ms,
                1 if log.user_confirmed else 0,
                now
            ))

            db_conn.commit()
            return cursor.lastrowid
        finally:
            db_conn.close()

    def get_audit_logs(self, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """
        Get audit logs with pagination.

        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip

        Returns:
            List of AuditLog objects ordered by created_at DESC
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ? OFFSET ?',
                (limit, offset)
            )
            rows = cursor.fetchall()
            return [self._row_to_audit_log(row) for row in rows]
        finally:
            db_conn.close()

    def get_audit_logs_by_session(self, session_id: int, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs for a specific session.

        Args:
            session_id: Session ID
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects ordered by created_at DESC
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM audit_logs WHERE session_id = ? ORDER BY created_at DESC LIMIT ?',
                (session_id, limit)
            )
            rows = cursor.fetchall()
            return [self._row_to_audit_log(row) for row in rows]
        finally:
            db_conn.close()

    def get_audit_logs_by_category(self, category: str, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs by category.

        Args:
            category: Log category (sql_execute, tool_call, config_change)
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects ordered by created_at DESC
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                'SELECT * FROM audit_logs WHERE category = ? ORDER BY created_at DESC LIMIT ?',
                (category, limit)
            )
            rows = cursor.fetchall()
            return [self._row_to_audit_log(row) for row in rows]
        finally:
            db_conn.close()

    def get_audit_logs_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[AuditLog]:
        """
        Get audit logs within a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects ordered by created_at DESC
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                '''SELECT * FROM audit_logs
                   WHERE created_at >= ? AND created_at <= ?
                   ORDER BY created_at DESC LIMIT ?''',
                (start_time.isoformat(), end_time.isoformat(), limit)
            )
            rows = cursor.fetchall()
            return [self._row_to_audit_log(row) for row in rows]
        finally:
            db_conn.close()

    def get_recent_sql_executions(self, limit: int = 50) -> List[AuditLog]:
        """
        Get recent SQL execution logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog objects for SQL executions
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                '''SELECT * FROM audit_logs
                   WHERE category = 'sql_execute'
                   ORDER BY created_at DESC LIMIT ?''',
                (limit,)
            )
            rows = cursor.fetchall()
            return [self._row_to_audit_log(row) for row in rows]
        finally:
            db_conn.close()

    def cleanup_old_audit_logs(self, days: int = 30) -> int:
        """
        Delete audit logs older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted logs
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute(
                'DELETE FROM audit_logs WHERE created_at < ?',
                (cutoff_date,)
            )
            deleted_count = cursor.rowcount
            db_conn.commit()
            return deleted_count
        finally:
            db_conn.close()

    def get_audit_log_count(self, category: str = None) -> int:
        """
        Get count of audit logs.

        Args:
            category: Optional category filter

        Returns:
            Number of audit logs
        """
        db_conn = self._get_connection()
        try:
            cursor = db_conn.cursor()
            if category:
                cursor.execute(
                    'SELECT COUNT(*) as count FROM audit_logs WHERE category = ?',
                    (category,)
                )
            else:
                cursor.execute('SELECT COUNT(*) as count FROM audit_logs')
            row = cursor.fetchone()
            return row['count'] if row else 0
        finally:
            db_conn.close()

    def _row_to_audit_log(self, row: sqlite3.Row) -> AuditLog:
        """Convert a database row to AuditLog object"""
        return AuditLog(
            id=row['id'],
            session_id=row['session_id'],
            connection_id=row['connection_id'],
            category=row['category'],
            action=row['action'],
            target_type=row['target_type'],
            target_name=row['target_name'],
            sql_text=row['sql_text'],
            parameters=row['parameters'],
            result_status=row['result_status'],
            result_summary=row['result_summary'],
            affected_rows=row['affected_rows'],
            execution_time_ms=row['execution_time_ms'],
            user_confirmed=bool(row['user_confirmed']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
