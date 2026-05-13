import json
from typing import Any, Dict, List

from backend.routers.models import SourceClassifierOutputList


def create_source_for_batch(
    source: List[Dict[str, Any]],
    company_id: str,
) -> SourceClassifierOutputList:
    output_sources: List[Dict[str, Any]] = []

    for item in source:
        if str(item.get("company_id", "")) != company_id:
            continue

        source_kind = str(item.get("source_kind", "")).upper()

        if source_kind == "FOLDER_UPLOAD":
            output_sources.append(
                {
                    "source_type": "FL",
                    "supported": True,
                    "params": {},
                }
            )
            continue

        if source_kind != "STRING":
            continue

        source_type = str(item.get("source_type", "")).upper()
        source_value = str(item.get("source_value", "")).strip()

        if source_type == "DB":

            parsed_value = json.loads(source_value)
            connection_url = str(parsed_value.get(
                "connection_url", source_value))
            connection_alias = str(parsed_value.get(
                "connection_alias", "default_connection"))
            db_type = str(parsed_value.get("db_type", "unknown"))

            output_sources.append(
                {
                    "source_type": "DB",
                    "supported": True,
                    "params": {
                        "connection_alias": connection_alias,
                        "connection_url": connection_url,
                        "db_type": db_type,
                    },
                }
            )
            continue

        if source_type == "WEB":
            web_url = source_value
            recommended_pages: List[str] = []

            try:
                parsed_value = json.loads(source_value)
                if isinstance(parsed_value, dict):
                    web_url = str(parsed_value.get("url", source_value)).strip()
                    raw_pages = parsed_value.get("recommended_pages", [])
                    if isinstance(raw_pages, list):
                        recommended_pages = [
                            str(page).strip()
                            for page in raw_pages
                            if str(page).strip()
                        ]
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

            output_sources.append(
                {
                    "source_type": "WEB",
                    "supported": True,
                    "params": {
                        "url": web_url,
                        "recommended_pages": recommended_pages,
                    },
                }
            )
            continue

        if source_type == "CSV":
            csv_path = source_value
            folder_path = ""
            delimiter = ","
            encoding = "utf-8"
            sample_rows = 5

            try:
                parsed_value = json.loads(source_value)
                if isinstance(parsed_value, dict):
                    csv_path = str(parsed_value.get("csv_path", source_value)).strip()
                    folder_path = str(parsed_value.get("folder_path", "")).strip()
                    delimiter = str(parsed_value.get("delimiter", ","))
                    encoding = str(parsed_value.get("encoding", "utf-8"))
                    sample_rows = int(parsed_value.get("sample_rows", 5))
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

            output_sources.append(
                {
                    "source_type": "CSV",
                    "supported": True,
                    "params": {
                        "csv_path": csv_path,
                        "folder_path": folder_path,
                        "delimiter": delimiter,
                        "encoding": encoding,
                        "sample_rows": sample_rows,
                    },
                }
            )
            continue

        output_sources.append(
            {
                "source_type": source_type or "unknown",
                "supported": True,
                "params": {"value": source_value},
            }
        )

    return SourceClassifierOutputList(sources=output_sources)
