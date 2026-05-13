from typing import Any, Dict, List


def _extract_documents(tool_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    extraction_result = tool_result.get("extraction_result", [])

    if isinstance(extraction_result, dict):
        documents = extraction_result.get("documents", [])
        return documents if isinstance(documents, list) else []

    if isinstance(extraction_result, list):
        return extraction_result

    return []


def normalize(tool_result: Dict[str, Any]) -> Dict[str, Any]:
    documents = _extract_documents(tool_result)

    content = [
        {
            "context": doc.get("content") or doc.get("context", ""),
            "data": {
                "name": doc.get("name", ""),
                "type": doc.get("type", ""),
                "error": doc.get("error"),
            },
        }
        for doc in documents
    ]

    summary = {
        "total_files_found": tool_result.get("total_files_found", len(content)),
        "extracted_files_count": len(content),
    }

    return {
        "status": tool_result.get("status", "unknown"),
        "summary": summary,
        "content": content,
    }
