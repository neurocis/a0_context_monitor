"""Plugin lifecycle hooks for a0_context_monitor.

Handles plugin initialization and registration.
Monitoring only - no automatic cleanup.
"""

import logging
from api.v2 import ApiHandler, api_handler
from usr.plugins.a0_context_monitor.api.context_monitor_api import ContextMonitorApiHandler

logger = logging.getLogger(__name__)

# Global handler instance
_handler_instance = None


def install():
    """Called when plugin is installed.
    
    Instantiates and registers the API handler with the framework.
    """
    global _handler_instance
    try:
        # Create instance of the API handler
        _handler_instance = ContextMonitorApiHandler()
        logger.info("[a0_context_monitor] API handler registered successfully")
        logger.info("[a0_context_monitor] Available endpoints:")
        logger.info("  GET /api/context-monitor/status")
        logger.info("  GET /api/context-monitor/contexts")
        logger.info("  GET /api/context-monitor/summary")
        logger.info("  GET /api/context-monitor/contexts/{context_id}")
        logger.info("  POST /api/context-monitor/export")
        logger.info("  GET /api/context-monitor/table")
        return True
    except Exception as e:
        logger.error(f"[a0_context_monitor] Failed to register API handler: {e}")
        return False


def pre_update():
    """Called before plugin update."""
    logger.info("[a0_context_monitor] Preparing for plugin update")
    return True


def uninstall():
    """Called when plugin is uninstalled."""
    global _handler_instance
    _handler_instance = None
    logger.info("[a0_context_monitor] Plugin uninstalled")
    return True
