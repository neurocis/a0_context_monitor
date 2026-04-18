"""Plugin lifecycle hooks for a0_context_monitor.

Handles plugin initialization and cleanup.
Monitoring only - no automatic cleanup of contexts.

Note: The ContextMonitorApiHandler is auto-discovered by the framework
from the api/ directory and registered automatically. This hook performs
post-install setup tasks only.
"""

import logging

logger = logging.getLogger(__name__)


def install(**kwargs):
    """Called when plugin is installed.
    
    The ContextMonitorApiHandler is auto-discovered by the framework
    from the api/ directory and registered automatically.
    This hook performs post-install setup tasks.
    
    Returns:
        bool: True if installation successful, False otherwise
    """
    try:
        logger.info("[a0_context_monitor] Installing context monitor plugin...")
        logger.info("[a0_context_monitor] Plugin installed successfully")
        logger.info("[a0_context_monitor] Available API action endpoints:")
        logger.info("  POST /api/plugins/a0_context_monitor/context_monitor_api")
        logger.info("    ?action=status     - Check if monitoring is available")
        logger.info("    ?action=contexts   - Get context inventory (add ?detailed=true)")
        logger.info("    ?action=summary    - Get context summary statistics")
        logger.info("    ?action=detail     - Get specific context details")
        logger.info("    ?action=export     - Export context inventory to file")
        logger.info("    ?action=table      - Get formatted summary table")
        return True
    except Exception as e:
        logger.error(f"[a0_context_monitor] Failed to install plugin: {e}")
        import traceback
        traceback.print_exc()
        return False


def pre_update(**kwargs):
    """Called before plugin update."""
    logger.info("[a0_context_monitor] Preparing for plugin update")
    return True


def uninstall(**kwargs):
    """Called when plugin is uninstalled."""
    logger.info("[a0_context_monitor] Plugin uninstalled")
    return True
