"""Core monitoring logic for AgentContext.

Works independently without modifying core framework code.
Uses ONLY existing public AgentContext methods: all() and get(id)
Monitoring only - no automatic cleanup.
"""

import logging
import sys
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

try:
    from agent import AgentContext
except ImportError:
    AgentContext = None

logger = logging.getLogger(__name__)



class ContextMonitorHelper:
    """Helper class providing context monitoring using only public AgentContext APIs."""

    @staticmethod
    def is_available() -> bool:
        """Check if AgentContext is available."""
        return AgentContext is not None

    @staticmethod
    def _estimate_context_size(context: Any) -> int:
        """Estimate memory size of a context object in bytes.
        
        Args:
            context: AgentContext object
            
        Returns:
            Estimated size in bytes
        """
        try:
            # Get size of the context object itself
            context_size = sys.getsizeof(context)
            
            # Add size of id, name, type strings
            if hasattr(context, 'id'):
                context_size += sys.getsizeof(context.id)
            if hasattr(context, 'name'):
                context_size += sys.getsizeof(context.name)
            if hasattr(context, 'type'):
                context_size += sys.getsizeof(context.type)
            if hasattr(context, 'created_at'):
                context_size += sys.getsizeof(context.created_at)
            if hasattr(context, 'last_message'):
                context_size += sys.getsizeof(context.last_message)
                
            # Add size of log (list of entries)
            if hasattr(context, 'log') and context.log:
                try:
                    log_size = sys.getsizeof(context.log)
                    if isinstance(context.log, list):
                        for entry in context.log[:100]:  # Sample first 100 entries
                            log_size += sys.getsizeof(entry)
                    context_size += log_size
                except Exception:
                    pass
                    
            # Add size of data dict
            if hasattr(context, 'data') and context.data:
                try:
                    data_size = sys.getsizeof(context.data)
                    if isinstance(context.data, dict):
                        for key, value in context.data.items():
                            data_size += sys.getsizeof(key)
                            data_size += sys.getsizeof(value)
                    context_size += data_size
                except Exception:
                    pass
            
            return context_size
        except Exception as e:
            logger.warning(f"Failed to estimate context size: {e}")
            return sys.getsizeof(context)

    @staticmethod
    def _context_to_dict(context: Any, detailed: bool = False) -> Dict[str, Any]:
        """Convert a context object to a dictionary.
        
        Args:
            context: AgentContext object
            detailed: Include detailed information
            
        Returns:
            Dictionary representation of context
        """
        try:
            size_bytes = ContextMonitorHelper._estimate_context_size(context)
            size_mb = size_bytes / (1024 * 1024)
            size_kb = size_bytes / 1024
            
            context_dict = {
                "id": getattr(context, 'id', 'unknown'),
                "name": getattr(context, 'name', 'unnamed'),
                "type": str(getattr(context, 'type', 'unknown')),
                "created_at": str(getattr(context, 'created_at', '')),
                "last_message": str(getattr(context, 'last_message', '')),
                "is_running": context.is_running() if hasattr(context, 'is_running') and callable(context.is_running) else False,
                "estimated_size_bytes": size_bytes,
                "estimated_size_kb": round(size_kb, 2),
                "estimated_size_mb": round(size_mb, 2),
            }
            
            if detailed:
                # Add detailed information
                log_entries = 0
                if hasattr(context, 'log') and context.log:
                    log_entries = len(context.log) if isinstance(context.log, list) else 0
                    
                data_keys = 0
                if hasattr(context, 'data') and context.data:
                    data_keys = len(context.data) if isinstance(context.data, dict) else 0
                    
                context_dict.update({
                    "log_entries": log_entries,
                    "data_keys": data_keys,
                })
            
            return context_dict
        except Exception as e:
            logger.error(f"Failed to convert context to dict: {e}")
            return {"id": "error", "error": str(e)}

    @staticmethod
    def get_contexts_inventory(
        detailed: bool = False,
    ) -> Dict[str, Any]:
        """Get context inventory using only public AgentContext APIs.

        Args:
            detailed: Include per-context details

        Returns:
            Dictionary with total_contexts, total_estimated_size_mb, contexts list, timestamp
        """
        if not ContextMonitorHelper.is_available():
            logger.error("AgentContext not available")
            return {
                "error": "AgentContext not available",
                "total_contexts": 0,
                "total_estimated_size_mb": 0.0,
                "total_estimated_size_bytes": 0,
                "contexts": [],
                "timestamp": datetime.now().isoformat(),
            }

        try:
            # Get all contexts using public API
            all_contexts = AgentContext.all()
            contexts_list = []
            total_size_bytes = 0
            
            for context in all_contexts:
                context_dict = ContextMonitorHelper._context_to_dict(context, detailed=detailed)
                contexts_list.append(context_dict)
                total_size_bytes += context_dict.get("estimated_size_bytes", 0)
            
            total_size_mb = total_size_bytes / (1024 * 1024)
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "total_contexts": len(contexts_list),
                "total_estimated_size_bytes": total_size_bytes,
                "total_estimated_size_mb": round(total_size_mb, 2),
                "contexts": contexts_list,
            }
        except Exception as e:
            logger.error(f"Failed to get contexts inventory: {e}", exc_info=True)
            return {
                "error": str(e),
                "total_contexts": 0,
                "total_estimated_size_mb": 0.0,
                "total_estimated_size_bytes": 0,
                "contexts": [],
                "timestamp": datetime.now().isoformat(),
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
            # Get inventory
            inventory = ContextMonitorHelper.get_contexts_inventory(detailed=True)
            
            # Use default path if not provided
            if file_path is None:
                file_path = "/tmp/agent_contexts_inventory.json"
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(inventory, f, indent=2, default=str)
            
            return {
                "status": "success",
                "message": "Context inventory exported successfully",
                "file_path": file_path,
                "total_contexts": inventory.get("total_contexts", 0),
            }
        except Exception as e:
            logger.error(f"Failed to export inventory: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "file_path": file_path,
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
                "total_estimated_size_bytes": 0,
                "running_contexts": 0,
                "idle_contexts": 0,
                "timestamp": datetime.now().isoformat(),
            }

        try:
            # Get inventory
            inventory = ContextMonitorHelper.get_contexts_inventory(detailed=False)
            contexts = inventory.get("contexts", [])

            # Count running and idle
            running_count = sum(1 for ctx in contexts if ctx.get("is_running", False))
            idle_count = len(contexts) - running_count

            return {
                "status": "success",
                "timestamp": inventory.get("timestamp", datetime.now().isoformat()),
                "total_contexts": inventory.get("total_contexts", 0),
                "total_estimated_size_bytes": inventory.get("total_estimated_size_bytes", 0),
                "total_estimated_size_mb": inventory.get("total_estimated_size_mb", 0.0),
                "running_contexts": running_count,
                "idle_contexts": idle_count,
            }
        except Exception as e:
            logger.error(f"Failed to get contexts summary: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "total_contexts": 0,
                "total_estimated_size_mb": 0.0,
                "total_estimated_size_bytes": 0,
                "running_contexts": 0,
                "idle_contexts": 0,
                "timestamp": datetime.now().isoformat(),
            }

    @staticmethod
    def get_context_by_id(context_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific context using public API.

        Args:
            context_id: The context ID to look up

        Returns:
            Context details or None if not found
        """
        if not ContextMonitorHelper.is_available():
            logger.error("AgentContext not available")
            return None

        try:
            # Use public AgentContext.get(id) API
            context = AgentContext.get(context_id)
            if context is None:
                return None
                
            return ContextMonitorHelper._context_to_dict(context, detailed=True)
        except Exception as e:
            logger.error(f"Failed to get context {context_id}: {e}", exc_info=True)
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
            inventory = ContextMonitorHelper.get_contexts_inventory(detailed=True)
            contexts = inventory.get("contexts", [])
            
            if not contexts:
                return "No contexts available"
            
            # Build table header
            lines = []
            lines.append("\n" + "="*120)
            lines.append(f"{'ID':<20} {'Name':<25} {'Type':<12} {'Size (MB)':<12} {'Status':<10} {'Created':<20}")
            lines.append("-"*120)
            
            # Build table rows
            for ctx in contexts:
                ctx_id = str(ctx.get("id", "?"))[:20]
                ctx_name = str(ctx.get("name", "?"))[:25]
                ctx_type = str(ctx.get("type", "?"))[:12]
                ctx_size = f"{ctx.get('estimated_size_mb', 0):.2f}"
                ctx_status = "running" if ctx.get("is_running", False) else "idle"
                ctx_created = str(ctx.get("created_at", "?"))[:20]
                
                lines.append(f"{ctx_id:<20} {ctx_name:<25} {ctx_type:<12} {ctx_size:<12} {ctx_status:<10} {ctx_created:<20}")
            
            # Add summary footer
            lines.append("-"*120)
            total_contexts = inventory.get("total_contexts", 0)
            total_size_mb = inventory.get("total_estimated_size_mb", 0.0)
            lines.append(f"Total: {total_contexts} contexts, {total_size_mb:.2f} MB")
            lines.append("="*120 + "\n")
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Failed to display summary: {e}", exc_info=True)
            return f"Error displaying summary: {e}"
