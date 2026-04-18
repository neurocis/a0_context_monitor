"""REST API handlers for context monitoring.

Provides FastA2A-compatible endpoints for querying context inventory,
summary statistics, and exporting context data.

Monitoring only - no automatic cleanup.
"""

import logging
import json
from typing import Dict, Any, Optional

from api.v2 import ApiHandler, api_handler
from usr.plugins.a0_context_monitor.helpers.monitor import ContextMonitorHelper

logger = logging.getLogger(__name__)


class ContextMonitorApiHandler(ApiHandler):
    """REST API handler for context monitoring endpoints."""

    def __init__(self):
        """Initialize the API handler."""
        super().__init__()
        self.monitor = ContextMonitorHelper

    @api_handler("GET", "/api/context-monitor/status")
    async def get_status(self, **kwargs) -> Dict[str, Any]:
        """Check if context monitoring is available.

        Returns:
            {"available": bool, "message": str}
        """
        available = self.monitor.is_available()
        return {
            "available": available,
            "message": "Context monitoring is available"
            if available
            else "AgentContext not available",
        }

    @api_handler("GET", "/api/context-monitor/contexts")
    async def get_contexts(
        self, detailed: bool = False, **kwargs
    ) -> Dict[str, Any]:
        """Get full context inventory.

        Query parameters:
            detailed (bool): Include per-context details

        Returns:
            Context inventory with total_contexts, total_estimated_size_mb, contexts list
        """
        detailed = str(detailed).lower() == "true"
        return self.monitor.get_contexts_inventory(detailed=detailed)

    @api_handler("GET", "/api/context-monitor/summary")
    async def get_summary(self, **kwargs) -> Dict[str, Any]:
        """Get context summary statistics.

        Returns:
            Summary with total_contexts, total_estimated_size_mb, running/idle counts, timestamp
        """
        return self.monitor.get_contexts_summary()

    @api_handler("GET", "/api/context-monitor/contexts/{context_id}")
    async def get_context_detail(self, context_id: str, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a specific context.

        Path parameters:
            context_id (str): The context ID to look up

        Returns:
            Context details or error if not found
        """
        context = self.monitor.get_context_by_id(context_id)
        if context is None:
            return {
                "error": f"Context {context_id} not found",
                "context_id": context_id,
            }
        return {"context": context, "found": True}

    @api_handler("POST", "/api/context-monitor/export")
    async def export_inventory(
        self, file_path: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Export context inventory to JSON file.

        Request body (optional):
            {"file_path": "/custom/path/to/file.json"}

        Returns:
            Status, message, and file path
        """
        return self.monitor.export_inventory_to_file(file_path=file_path)

    @api_handler("GET", "/api/context-monitor/table")
    async def get_summary_table(self, **kwargs) -> Dict[str, Any]:
        """Get formatted context summary table as string.

        Returns:
            {"table": formatted_string, "status": "success" or "error"}
        """
        table = self.monitor.display_summary_table()
        return {"table": table, "status": "success"}
