from typing import Any, Dict


def _normalize_single_file(tool_result: Dict[str, Any]) -> Dict[str, Any]:
    schema_result = tool_result.get("schema_result", {})
    columns = schema_result.get("columns", [])
    sample_rows = tool_result.get("sample_result", [])
    file_info = tool_result.get("file_info", {})

    content_entries = [
        {
            "item_type": "csv_column",
            "data": {
                "file_name": file_info.get("name", ""),
                "table_name": file_info.get("table_name", ""),
                **column,
            },
        }
        for column in columns
    ]

    if sample_rows:
        content_entries.append(
            {
                "item_type": "csv_sample_rows",
                "data": {
                    "file_name": file_info.get("name", ""),
                    "table_name": file_info.get("table_name", ""),
                    "rows": sample_rows,
                },
            }
        )

    summary = {
        "file_name": file_info.get("name", ""),
        "table_name": file_info.get("table_name", ""),
        "rows_count": schema_result.get("total_rows", 0),
        "columns_count": schema_result.get("total_columns", len(columns)),
    }

    return {
        "status": tool_result.get("status", "unknown"),
        "summary": summary,
        "content": content_entries,
    }


def normalize(tool_result: Dict[str, Any]) -> Dict[str, Any]:
    files = tool_result.get("files")
    if isinstance(files, list):
        content_entries: list[Dict[str, Any]] = []
        successful_files = 0

        for file_result in files:
            normalized = _normalize_single_file(file_result)
            if normalized.get("status") == "success":
                successful_files += 1
            content_entries.extend(normalized.get("content", []))

        folder_info = tool_result.get("folder_info", {})
        summary = {
            "folder_path": folder_info.get("path", ""),
            "total_csv_files": folder_info.get("total_csv_files", len(files)),
            "successful_files": successful_files,
        }
        return {
            "status": tool_result.get("status", "unknown"),
            "summary": summary,
            "content": content_entries,
        }

    return _normalize_single_file(tool_result)
