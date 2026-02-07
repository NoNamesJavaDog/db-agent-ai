"""
Tool Registry - Unified tool definitions with i18n support

Eliminates duplicated EN/ZH tool definitions by using i18n keys.
"""
from typing import Dict, List, Any
from db_agent.i18n import t


# Tool parameter definitions (language-independent)
_TOOL_PARAMS = {
    "identify_slow_queries": {
        "type": "object",
        "properties": {
            "min_duration_ms": {"type": "number"},
            "limit": {"type": "integer"}
        }
    },
    "get_running_queries": {
        "type": "object",
        "properties": {}
    },
    "run_explain": {
        "type": "object",
        "properties": {
            "sql": {"type": "string"},
            "analyze": {"type": "boolean"}
        },
        "required": ["sql"]
    },
    "check_index_usage": {
        "type": "object",
        "properties": {
            "table_name": {"type": "string"},
            "schema": {"type": "string"}
        },
        "required": ["table_name"]
    },
    "get_table_stats": {
        "type": "object",
        "properties": {
            "table_name": {"type": "string"},
            "schema": {"type": "string"}
        },
        "required": ["table_name"]
    },
    "create_index": {
        "type": "object",
        "properties": {
            "index_sql": {"type": "string"},
            "concurrent": {"type": "boolean"}
        },
        "required": ["index_sql"]
    },
    "analyze_table": {
        "type": "object",
        "properties": {
            "table_name": {"type": "string"},
            "schema": {"type": "string"}
        },
        "required": ["table_name"]
    },
    "execute_safe_query": {
        "type": "object",
        "properties": {
            "sql": {"type": "string"}
        },
        "required": ["sql"]
    },
    "execute_sql": {
        "type": "object",
        "properties": {
            "sql": {"type": "string"}
        },
        "required": ["sql"]
    },
    "list_tables": {
        "type": "object",
        "properties": {
            "schema": {"type": "string"}
        }
    },
    "describe_table": {
        "type": "object",
        "properties": {
            "table_name": {"type": "string"},
            "schema": {"type": "string"}
        },
        "required": ["table_name"]
    },
    "get_sample_data": {
        "type": "object",
        "properties": {
            "table_name": {"type": "string"},
            "schema": {"type": "string"},
            "limit": {"type": "integer"}
        },
        "required": ["table_name"]
    },
    "list_databases": {
        "type": "object",
        "properties": {
            "schema": {"type": "string"}
        }
    },
    "switch_database": {
        "type": "object",
        "properties": {
            "database": {"type": "string"}
        },
        "required": ["database"]
    },
}

_MIGRATION_TOOL_PARAMS = {
    "analyze_source_database": {
        "type": "object",
        "properties": {
            "source_connection_name": {"type": "string"},
            "schema": {"type": "string"},
            "object_types": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["source_connection_name"]
    },
    "create_migration_plan": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer"},
            "source_connection_name": {"type": "string"},
            "target_schema": {"type": "string"}
        },
        "required": ["task_id", "source_connection_name"]
    },
    "get_migration_plan": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer"}
        },
        "required": ["task_id"]
    },
    "get_migration_status": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer"}
        },
        "required": ["task_id"]
    },
    "execute_migration_item": {
        "type": "object",
        "properties": {
            "item_id": {"type": "integer"}
        },
        "required": ["item_id"]
    },
    "execute_migration_batch": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer"},
            "batch_size": {"type": "integer"}
        },
        "required": ["task_id"]
    },
    "compare_databases": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer"}
        },
        "required": ["task_id"]
    },
    "generate_migration_report": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer"}
        },
        "required": ["task_id"]
    },
    "skip_migration_item": {
        "type": "object",
        "properties": {
            "item_id": {"type": "integer"},
            "reason": {"type": "string"}
        },
        "required": ["item_id"]
    },
    "retry_failed_items": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer"}
        },
        "required": ["task_id"]
    },
    "request_migration_setup": {
        "type": "object",
        "properties": {
            "reason": {"type": "string"},
            "suggested_source_db_type": {"type": "string"},
            "suggested_target_db_type": {"type": "string"},
        },
        "required": ["reason"]
    },
}

_INTERACTION_TOOL_PARAMS = {
    "request_user_input": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Form title shown to the user"},
            "description": {"type": "string", "description": "Brief description of what the form is for"},
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "label": {"type": "string"},
                        "type": {"type": "string", "enum": ["text", "number", "select", "textarea", "date"]},
                        "required": {"type": "boolean"},
                        "placeholder": {"type": "string"},
                        "options": {"type": "array", "items": {"type": "string"}, "description": "For select type only"}
                    },
                    "required": ["name", "label", "type"]
                }
            }
        },
        "required": ["title", "fields"]
    },
}

# i18n keys for tool descriptions (tool_desc_<name>) and parameter descriptions (tool_param_<name>_<param>)
DB_TOOL_NAMES = list(_TOOL_PARAMS.keys())
MIGRATION_TOOL_NAMES = list(_MIGRATION_TOOL_PARAMS.keys())


def _build_param_descriptions(tool_name: str, params: dict) -> dict:
    """Build parameters with localized descriptions."""
    result = {
        "type": params["type"],
        "properties": {}
    }
    for prop_name, prop_def in params.get("properties", {}).items():
        prop_copy = dict(prop_def)
        desc_key = f"tool_param_{tool_name}_{prop_name}"
        prop_copy["description"] = t(desc_key)
        result["properties"][prop_name] = prop_copy
    if "required" in params:
        result["required"] = params["required"]
    return result


def build_tools(language: str = None) -> List[Dict[str, Any]]:
    """
    Build tool definitions with localized descriptions.

    Args:
        language: Language code (unused - uses global i18n state)

    Returns:
        List of tool definitions in OpenAI function format
    """
    tools = []

    # DB tools
    for tool_name, params in _TOOL_PARAMS.items():
        desc_key = f"tool_desc_{tool_name}"
        tools.append({
            "type": "function",
            "function": {
                "name": tool_name,
                "description": t(desc_key),
                "parameters": _build_param_descriptions(tool_name, params)
            }
        })

    # Migration tools
    for tool_name, params in _MIGRATION_TOOL_PARAMS.items():
        desc_key = f"tool_desc_{tool_name}"
        tools.append({
            "type": "function",
            "function": {
                "name": tool_name,
                "description": t(desc_key),
                "parameters": _build_param_descriptions(tool_name, params)
            }
        })

    # Interaction tools (request_user_input, etc.)
    for tool_name, params in _INTERACTION_TOOL_PARAMS.items():
        desc_key = f"tool_desc_{tool_name}"
        tools.append({
            "type": "function",
            "function": {
                "name": tool_name,
                "description": t(desc_key),
                "parameters": params  # descriptions are inline for this tool
            }
        })

    return tools
