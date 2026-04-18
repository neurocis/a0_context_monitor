"""Token tracking state for context monitoring.

Stores per-context token breakdowns from the last inference cycle.
Keyed by context_id, updated by python extensions, read by API handler.
"""

import threading
from typing import Dict, Any, Optional

_lock = threading.Lock()
_token_data: Dict[str, Dict[str, int]] = {}


def update_tokens(
    context_id: str,
    system_tokens: int = 0,
    context_tokens: int = 0,
    prompt_tokens: int = 0,
    response_tokens: int = 0,
) -> None:
    """Update token counts for a given context.

    Args:
        context_id: The context identifier
        system_tokens: Tokens from system prompt strings
        context_tokens: Tokens from conversation history
        prompt_tokens: Total prompt tokens (system + context)
        response_tokens: Tokens from the LLM response
    """
    with _lock:
        _token_data[context_id] = {
            "system_tokens": system_tokens,
            "context_tokens": context_tokens,
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": system_tokens + context_tokens + response_tokens,
        }


def get_tokens(context_id: str) -> Optional[Dict[str, int]]:
    """Get token counts for a given context.

    Args:
        context_id: The context identifier

    Returns:
        Dict with token breakdown or None if not found
    """
    with _lock:
        return _token_data.get(context_id)


def get_all_tokens() -> Dict[str, Dict[str, int]]:
    """Get token counts for all contexts.

    Returns:
        Dict mapping context_id to token breakdown
    """
    with _lock:
        return dict(_token_data)


def clear_tokens(context_id: str) -> None:
    """Clear token counts for a given context.

    Args:
        context_id: The context identifier
    """
    with _lock:
        _token_data.pop(context_id, None)
