"""Token capture extension - message_loop_prompts_after hook.

Hook: message_loop_prompts_after (priority 10)
Captures system and context token counts after prompts are assembled,
then stores them in token_state for API retrieval.
"""

import json
import logging
from helpers.extension import Extension
from helpers.tokens import approximate_tokens
from usr.plugins.a0_context_monitor.helpers.token_state import update_tokens, get_tokens

logger = logging.getLogger(__name__)


class CaptureTokens(Extension):

    async def execute(self, **kwargs):
        loop_data = kwargs.get("loop_data", None)
        if loop_data is None:
            return

        try:
            context_id = self.agent.context.id if hasattr(self.agent, "context") else None
            if not context_id:
                return

            # Compute system tokens from loop_data.system (list of strings)
            system_tokens = 0
            if hasattr(loop_data, "system") and loop_data.system:
                for sys_str in loop_data.system:
                    if isinstance(sys_str, str) and sys_str:
                        system_tokens += approximate_tokens(sys_str)

            # Compute context tokens from loop_data.history_output (list of OutputMessage)
            context_tokens = 0
            if hasattr(loop_data, "history_output") and loop_data.history_output:
                for msg in loop_data.history_output:
                    content = msg.get("content", "") if isinstance(msg, dict) else ""
                    if isinstance(content, str) and content:
                        context_tokens += approximate_tokens(content)
                    elif content:
                        # Content is list/dict - serialize first
                        try:
                            content_str = json.dumps(content)
                            context_tokens += approximate_tokens(content_str)
                        except (TypeError, ValueError):
                            pass

            # Prompt tokens = system + context
            prompt_tokens = system_tokens + context_tokens

            # Preserve existing response_tokens if already set
            existing = get_tokens(context_id)
            response_tokens = existing.get("response_tokens", 0) if existing else 0

            update_tokens(
                context_id=context_id,
                system_tokens=system_tokens,
                context_tokens=context_tokens,
                prompt_tokens=prompt_tokens,
                response_tokens=response_tokens,
            )

        except Exception as e:
            logger.error(f"Error capturing tokens: {e}", exc_info=True)
