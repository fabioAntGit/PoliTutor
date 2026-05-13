from pathlib import Path
from typing import Any, Dict

import pandas as pd


def _resolve_csv_path(params: Dict[str, Any]) -> Path | None:
    raw_path = (
        params.get("csv_path")
        or params.get("path")
        or params.get("file_path")
        or params.get("value")
    )

    if not raw_path:
        return None

    return Path(str(raw_path)).expanduser().resolve()


def _resolve_csv_folder(params: Dict[str, Any]) -> Path | None:
    raw_folder = params.get("folder_path") or params.get("csv_folder")
    if not raw_folder:
        return None
    return Path(str(raw_folder)).expanduser().resolve()


def _build_columns_schema(dataframe: pd.DataFrame) -> list[Dict[str, Any]]:
    columns: list[Dict[str, Any]] = []

    for column_name in dataframe.columns:
        series = dataframe[column_name]
        columns.append(
            {
                "name": str(column_name),
                "type": str(series.dtype),
                "nullable": bool(series.isnull().any()),
                "non_null_count": int(series.notna().sum()),
                "null_count": int(series.isna().sum()),
            }
        )

    return columns


def _extract_single_csv(csv_path: Path, delimiter: str, encoding: str, sample_rows: int) -> Dict[str, Any]:
    dataframe = pd.read_csv(csv_path, sep=delimiter, encoding=encoding)
    columns = _build_columns_schema(dataframe)

    return {
        "status": "success",
        "file_info": {
            "name": csv_path.name,
            "path": str(csv_path),
            "table_name": csv_path.stem,
        },
        "schema_result": {
            "columns": columns,
            "total_columns": len(columns),
            "total_rows": int(len(dataframe)),
        },
        "sample_result": dataframe.head(sample_rows).to_dict(orient="records"),
    }


def extract_csv_context(params: Dict[str, Any]) -> Dict[str, Any]:
    folder_path = _resolve_csv_folder(params)
    csv_path = _resolve_csv_path(params)
    if folder_path is None and csv_path is None:
        return {
            "status": "error",
            "message": "Missing CSV source. Use csv_path for a file or folder_path for a folder.",
        }

    delimiter = str(params.get("delimiter", ","))
    encoding = str(params.get("encoding", "utf-8"))

    try:
        sample_rows = int(params.get("sample_rows", 5))
    except (TypeError, ValueError):
        sample_rows = 5

    sample_rows = max(1, min(sample_rows, 50))

    if folder_path is not None:
        if not folder_path.exists() or not folder_path.is_dir():
            return {
                "status": "error",
                "message": f"CSV folder not found: {folder_path}",
            }

        csv_files = sorted(path for path in folder_path.rglob("*.csv") if path.is_file())
        if not csv_files:
            return {
                "status": "error",
                "message": f"No .csv files found in folder: {folder_path}",
            }

        files_result: list[Dict[str, Any]] = []
        for csv_file in csv_files:
            try:
                files_result.append(
                    _extract_single_csv(
                        csv_path=csv_file,
                        delimiter=delimiter,
                        encoding=encoding,
                        sample_rows=sample_rows,
                    )
                )
            except Exception as error:
                files_result.append(
                    {
                        "status": "error",
                        "file_info": {
                            "name": csv_file.name,
                            "path": str(csv_file),
                            "table_name": csv_file.stem,
                        },
                        "message": f"CSV extraction failed: {str(error)}",
                    }
                )

        success_count = sum(1 for item in files_result if item.get("status") == "success")

        return {
            "status": "success" if success_count > 0 else "error",
            "folder_info": {
                "path": str(folder_path),
                "total_csv_files": len(csv_files),
            },
            "files": files_result,
        }

    if csv_path is None or not csv_path.exists() or not csv_path.is_file():
        return {
            "status": "error",
            "message": f"CSV file not found: {csv_path}",
        }

    try:
        return _extract_single_csv(
            csv_path=csv_path,
            delimiter=delimiter,
            encoding=encoding,
            sample_rows=sample_rows,
        )
    except Exception as error:
        return {
            "status": "error",
            "message": f"CSV extraction failed: {str(error)}",
        }


def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    return extract_csv_context(params)


if __name__ == "__main__":
    # Example usage
    result = execute({"csv_path": "./example.csv", "sample_rows": 3})
    print(result)
