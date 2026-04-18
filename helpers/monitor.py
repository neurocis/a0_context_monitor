"""Core monitoring logic for AgentContext.

Wraps AgentContext monitoring methods to provide interface for REST API and webui.
Monitoring only - no automatic cleanup.
"""

import logging
from typing import Dict, Any, List, Optional

try:
    from agent import AgentContext
except ImportError:
    AgentContext = None

logger = logging.getLogger(__name__)


class ContextMonitorHelper:
    """Helper class exposing AgentContext monitoring capabilities."""

    @staticmethod
    def is_available() -> bool:
        """Check if AgentContext monitoring is available."""
        return AgentContext is not None

    @staticmethod
    def get_contexts_inventory(
        detailed: bool = False,
    ) -> Dict[str, Any]:
        """Get context inventory from AgentContext.

        Args:
            detailed: Include per-context details

        Returns:
            Dictionary with total_contexts, total_estimated_size_mb, contexts list
        """
        if not ContextMonitorHelper.is_available():
            logger.error("AgentContext not available")
            return {
                "error": "AgentContext not available",
                "total_contexts": 0,
                "total_estimated_size_mb": 0.0,
                "contexts": [],
            }

        try:
            inventory = AgentContext.get_contexts_info(detailed=detailed)
            return inventory
        except Exception as e:
            logger.error(f"Failed to get contexts inventory: {e}")
            return {
                "error": str(e),
                "total_contexts": 0,
                "total_estimated_size_mb": 0.0,
                "contexts": [],
            }

    @staticmethod
    def export_inventory_to_file(file_path: Optional[str] = None) -> Dict[str, Any]:
        """Export context inventory to JSON file.

        Args:
            file_path: Optional custom file path. If None, uses default.

        Returns:
            Result dictionary with status, file_path, total_contexts
        """
        if not ContextMonitorHelper.is_available():
            return {
                "status": "error",
                "message": "AgentContext not available",
                "file_path": None,
            }

        try:
            AgentContext.dump_contexts_info(file_path=file_path)
            return {
                "status": "success",
                "message": "Context inventory exported successfully",
                "file_path": file_path or "/tmp/agent_contexts_inventory.json",
            }
        except Exception as e:
            logger.error(f"Failed to export inventory: {e}")
            return {
                "status": "error",
                "message": str(e),
                "file_path": None,
            }

    @staticmethod
    def get_contexts_summary() -> Dict[str, Any]:
        """Get summary statistics about contexts.

        Returns:
            Summary dictionary with counts and sizes
        """
        if not ContextMonitorHelper.is_available():
            return {
                "status": "error",
                "message": "AgentContext not available",
                "total_contexts": 0,
                "total_estimated_size_mb": 0.0,
                "running_contexts": 0,
                "idle_contexts": 0,
            }

        try:
            inventory = AgentContext.get_contexts_info(detailed=True)
            contexts = inventory.get("contexts", [])

            running_count = sum(1 for ctx in contexts if ctx.get("is_running", False))
            idle_count = len(contexts) - running_count

            return {
                "status": "success",
                "total_contexts": inventory.get("total_contexts", 0),
                "total_estimated_size_mb": inventory.get(
                    "total_estimated_size_mb", 0.0
                ),
                "running_contexts": running_count,
                "idle_contexts": idle_count,
                "timestamp": inventory.get("timestamp"),
            }
        except Exception as e:
            logger.error(f"Failed to get contexts summary: {e}")
            return {
                "status": "error",
                "message": str(e),
                "total_contexts": 0,
                "total_estimated_size_mb": 0.0,
                "running_contexts": 0,
                "idle_contexts": 0,
            }

    @staticmethod
    def get_context_by_id(context_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific context.

        Args:
            context_id: The context ID to look up

        Returns:
            Context details or None if not found
        """
        if not ContextMonitorHelper.is_available():
            logger.error("AgentContext not available")
            return None

        try:
            inventory = AgentContext.get_contexts_info(detailed=True)
            for context in inventory.get("contexts", []):
                if context.get("id") == context_id:
                    return context
            return None
        except Exception as e:
            logger.error(f"Failed to get context {context_id}: {e}")
            return None

    @staticmethod
    def display_summary_table() -> str:
        """Get formatted summary table as string.

        Returns:
            Formatted table string
        """
        if not ContextMonitorHelper.is_available():
            return "AgentContext not available"

        try:
            # This calls the built-in display method
            # which returns a formatted string
            import io
            import sys

            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()

            try:
                AgentContext.display_contexts_summary()
                output = buffer.getvalue()
            finally:
                sys.stdout = old_stdout

            return output
        except Exception as e:
            logger.error(f"Failed to display summary: {e}")
            return f"Error displaying summary: {e}"
