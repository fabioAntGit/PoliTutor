from typing import Any, Dict


def normalize(tool_result: Dict[str, Any]) -> Dict[str, Any]:
    profile_blocks = tool_result.get("profile_blocks", [])

    content = [
        {
            "data": {
                "url": block.get("url", ""),
                "sections": block.get("sections", []),
            }
        }
        for block in profile_blocks
    ]

    summary = {
        "base_url": tool_result.get("base_url"),
        "profile_blocks_count": len(content),
    }

    return {
        "status": tool_result.get("status", "unknown"),
        "summary": summary,
        "content": content,
    }
