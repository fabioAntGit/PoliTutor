from typing import Any, Dict


def normalize(tool_result: Dict[str, Any]) -> Dict[str, Any]:
    schema_tables = tool_result.get("schema_result", {}).get("tables", [])
    table_permissions = tool_result.get(
        "permissions_result", {}).get("company_context_format", [])

    content_entries = [
        {
            "item_type": "db_table",
            "data": table,
        }
        for table in schema_tables
    ]

    content_entries.extend(
        [
            {
                "item_type": "db_permissions",
                "data": table_permissions_entry,
            }
            for table_permissions_entry in table_permissions
        ]
    )

    summary = {
        "tables_count": len(schema_tables),
        "permissions_entries_count": len(table_permissions),
        "connection_status": tool_result.get("connection_result", {}).get("status", "unknown"),
    }

    return {
        "status": tool_result.get("status", "unknown"),
        "summary": summary,
        "content": content_entries,
    }
