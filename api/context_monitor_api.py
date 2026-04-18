"""REST API handlers for context monitoring.

Provides FastA2A-compatible endpoints for querying context inventory,
summary statistics, and exporting context data.

Monitoring only - no automatic cleanup.
"""

import logging
import json
from typing import Dict, Any, Optional

from helpers.api import ApiHandler, Input, Output, Request, Response
from usr.plugins.a0_context_monitor.helpers.monitor import ContextMonitorHelper

logger = logging.getLogger(__name__)


class ContextMonitorApiHandler(ApiHandler):
    """REST API handler for context monitoring endpoints."""

    def __init__(self):
        """Initialize the API handler."""
        super().__init__()
        self.monitor = ContextMonitorHelper

    async def process(self, input: Input, request: Request) -> Output:
        """Main entry point for API requests.

        Routes requests based on the endpoint path.
        """
        path = request.path if hasattr(request, 'path') else ''
        method = request.method if hasattr(request, 'method') else 'GET'
        action = input.get('action', 'status') if isinstance(input, dict) else 'status'
        
        try:
            # Route handlers based on action parameter
            if action == 'status':
                return await self._get_status()
            elif action == 'contexts':
                detailed = input.get('detailed', False) if isinstance(input, dict) else False
                return await self._get_contexts(detailed=detailed)
            elif action == 'summary':
                return await self._get_summary()
            elif action == 'detail':
                context_id = input.get('context_id', '') if isinstance(input, dict) else ''
                return await self._get_context_detail(context_id)
            elif action == 'export':
                file_path = input.get('file_path', None) if isinstance(input, dict) else None
                return await self._export_contexts(file_path)
            elif action == 'table':
                return await self._get_table()
            else:
                return Response(f"Unknown action: {action}", 400)
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            return Response(f"Internal server error: {str(e)}", 500)

    async def _get_status(self) -> Dict[str, Any]:
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

    async def _get_contexts(self, detailed: bool = False) -> Dict[str, Any]:
        """Get full context inventory.

        Args:
            detailed (bool): Include per-context details

        Returns:
            Context inventory with total_contexts, total_estimated_size_mb, contexts list
        """
        return self.monitor.get_contexts_inventory(detailed=detailed)

    async def _get_summary(self) -> Dict[str, Any]:
        """Get context summary statistics.

        Returns:
            Summary with total_contexts, total_estimated_size_mb, running/idle counts, timestamp
        """
        return self.monitor.get_contexts_summary()

    async def _get_context_detail(self, context_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific context.

        Args:
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

    async def _export_contexts(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Export context inventory to JSON file.

        Args:
            file_path (str, optional): Custom file path for export

        Returns:
            Status, message, and file path
        """
        return self.monitor.export_inventory_to_file(file_path=file_path)

    async def _get_table(self) -> Dict[str, Any]:
        """Get formatted context summary table as string.

        Returns:
            {"table": formatted_string, "status": "success" or "error"}
        """
        table = self.monitor.display_summary_table()
        return {"table": table, "status": "success"}
