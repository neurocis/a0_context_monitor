"""Plugin lifecycle hooks for a0_context_monitor.

Handles plugin initialization and registration.
Monitoring only - no automatic cleanup.
"""

import logging

logger = logging.getLogger(__name__)


def install():
    """Called when plugin is installed."""
    logger.info("[a0_context_monitor] Plugin installed successfully")
    return True


def pre_update():
    """Called before plugin update."""
    logger.info("[a0_context_monitor] Preparing for plugin update")
    return True


def uninstall():
    """Called when plugin is uninstalled."""
    logger.info("[a0_context_monitor] Plugin uninstalled")
    return True
