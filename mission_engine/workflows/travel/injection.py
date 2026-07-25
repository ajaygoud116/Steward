from typing import Optional, Any

_INJECTION_TOOL = None


def inject_tool_failure(tool: str, error: str):
    global _INJECTION_TOOL
    _INJECTION_TOOL = (tool, error)


def clear_injection():
    global _INJECTION_TOOL
    _INJECTION_TOOL = None


def should_fail(tool: str) -> Optional[str]:
    global _INJECTION_TOOL
    if _INJECTION_TOOL and _INJECTION_TOOL[0] == tool:
        return _INJECTION_TOOL[1]
    return None


def inject_malformed_output(tool: str, output: Any) -> Any:
    global _INJECTION_TOOL
    if _INJECTION_TOOL and _INJECTION_TOOL[0] == f"malformed_{tool}":
        return _INJECTION_TOOL[1]
    return output
