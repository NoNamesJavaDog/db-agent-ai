// ─── Connection Types ────────────────────────────────────────────────────

export interface Connection {
  id: number;
  name: string;
  db_type: string;
  host: string;
  port: number;
  database: string;
  username: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ConnectionCreate {
  name: string;
  db_type: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
}

export interface ConnectionUpdate {
  name?: string;
  db_type?: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  db_info?: Record<string, any>;
}

export interface DatabaseInfo {
  name: string;
  size?: string;
  owner?: string;
  is_current?: boolean;
}

export interface DatabaseListResponse {
  databases: DatabaseInfo[];
  current_database: string;
  instance: string;
}

// ─── Provider Types ──────────────────────────────────────────────────────

export interface Provider {
  id: number;
  name: string;
  provider: string;
  model: string;
  base_url?: string;
  is_default: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ProviderCreate {
  name: string;
  provider: string;
  api_key: string;
  model?: string;
  base_url?: string;
}

export interface ProviderUpdate {
  name?: string;
  provider?: string;
  api_key?: string;
  model?: string;
  base_url?: string;
}

export interface AvailableProvider {
  key: string;
  name: string;
  default_model: string;
  base_url?: string;
}

// ─── Session Types ───────────────────────────────────────────────────────

export interface Session {
  id: number;
  name: string;
  connection_id?: number;
  provider_id?: number;
  is_current: boolean;
  message_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface SessionCreate {
  name?: string;
  connection_id?: number;
  provider_id?: number;
}

export interface Message {
  id: number;
  session_id: number;
  role: 'user' | 'assistant' | 'tool';
  content?: string;
  tool_calls?: string;
  tool_call_id?: string;
  created_at?: string;
}

// ─── Chat Types ──────────────────────────────────────────────────────────

export type MessagePart =
  | { type: 'text'; content: string }
  | { type: 'tool'; toolIndex: number };

export interface MigrationSetup {
  reason: string;
  suggested_source_db_type?: string;
  suggested_target_db_type?: string;
}

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'textarea' | 'date';
  required?: boolean;
  placeholder?: string;
  options?: string[];  // for select type
}

export interface FormInputRequest {
  title: string;
  description?: string;
  fields: FormField[];
}

export interface MigrationProgress {
  task_id: number;
  total: number;
  completed: number;
  failed: number;
  skipped: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  toolCalls?: ToolCall[];
  parts?: MessagePart[];
  pending?: PendingOperation[];
  migrationSetup?: MigrationSetup;
  migrationProgress?: MigrationProgress;
  formInput?: FormInputRequest;
  isStreaming?: boolean;
}

export interface ToolCall {
  name: string;
  input: Record<string, any>;
  status?: 'running' | 'success' | 'error';
  summary?: string;
}

export interface PendingOperation {
  index: number;
  type: string;
  sql?: string;
  description?: string;
}

// ─── MCP Types ───────────────────────────────────────────────────────────

export interface McpServer {
  id?: number;
  name: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
  enabled: boolean;
  connected: boolean;
  tool_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface McpServerCreate {
  name: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
}

export interface McpTool {
  name: string;
  description: string;
  server_name: string;
  input_schema?: Record<string, any>;
}

// ─── Skill Types ─────────────────────────────────────────────────────────

export interface Skill {
  name: string;
  description: string;
  source: string;
  user_invocable: boolean;
  model_invocable: boolean;
}

export interface SkillDetail extends Skill {
  instructions: string;
}

// ─── Migration Types ─────────────────────────────────────────────────────

export interface MigrationTask {
  id: number;
  name: string;
  source_connection_id: number;
  target_connection_id: number;
  source_db_type: string;
  target_db_type: string;
  status: string;
  total_items: number;
  completed_items: number;
  failed_items: number;
  skipped_items: number;
  source_schema?: string;
  target_schema?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MigrationTaskCreate {
  name: string;
  source_connection_id: number;
  target_connection_id: number;
  source_schema?: string;
  target_schema?: string;
  options?: Record<string, any>;
}

export interface MigrationItem {
  id: number;
  task_id: number;
  object_type: string;
  object_name: string;
  schema_name?: string;
  execution_order: number;
  status: string;
  source_ddl?: string;
  target_ddl?: string;
  conversion_notes?: string;
  error_message?: string;
  retry_count: number;
  executed_at?: string;
  created_at?: string;
}

// ─── Settings Types ──────────────────────────────────────────────────────

export interface Settings {
  language: string;
  theme: string;
}

// ─── Audit Types ─────────────────────────────────────────────────────────

export interface AuditLog {
  id: number;
  session_id?: number;
  connection_id?: number;
  category: string;
  action: string;
  target_type?: string;
  target_name?: string;
  sql_text?: string;
  result_status: string;
  result_summary?: string;
  affected_rows?: number;
  execution_time_ms?: number;
  user_confirmed: boolean;
  created_at?: string;
}

// ─── Health Types ────────────────────────────────────────────────────────

export interface HealthStatus {
  status: string;
  active_sessions: number;
  total_connections: number;
  total_providers: number;
  mcp_servers: number;
  skills_loaded: number;
  timestamp: string;
}

// ─── Generic Types ───────────────────────────────────────────────────────

export interface SuccessResponse {
  success: boolean;
  message: string;
}
