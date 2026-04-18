"""Token capture extension - response_stream_end hook.

Hook: response_stream_end (priority 10)
Captures response token count after streaming ends,
then updates token_state with the response breakdown.
"""

import json
import logging
from helpers.extension import Extension
from helpers.tokens import approximate_tokens
from usr.plugins.a0_context_monitor.helpers.token_state import update_tokens, get_tokens

logger = logging.getLogger(__name__)


class CaptureResponseTokens(Extension):

    async def execute(self, **kwargs):
        loop_data = kwargs.get("loop_data", None)
        if loop_data is None:
            return

        try:
            context_id = self.agent.context.id if hasattr(self.agent, "context") else None
            if not context_id:
                return

            # Get the last response text from loop_data
            response_text = ""
            if hasattr(loop_data, "last_response") and loop_data.last_response:
                response_text = str(loop_data.last_response)

            # Fallback: try to get the last AI message from history
            if not response_text and hasattr(self.agent, "history"):
                try:
                    history_output = self.agent.history.output()
                    if history_output:
                        # Find the last AI message
                        for msg in reversed(history_output):
                            if isinstance(msg, dict) and msg.get("ai"):
                                content = msg.get("content", "")
                                if isinstance(content, str):
                                    response_text = content
                                elif content:
                                    response_text = json.dumps(content)
                                if response_text:
                                    break
                except Exception:
                    pass

            # Compute response tokens
            response_tokens = 0
            if response_text:
                response_tokens = approximate_tokens(response_text)

            # Preserve existing prompt tokens from the prompts_after capture
            existing = get_tokens(context_id) or {}
            system_tokens = existing.get("system_tokens", 0)
            context_tokens = existing.get("context_tokens", 0)
            prompt_tokens = existing.get("prompt_tokens", 0)

            update_tokens(
                context_id=context_id,
                system_tokens=system_tokens,
                context_tokens=context_tokens,
                prompt_tokens=prompt_tokens,
                response_tokens=response_tokens,
            )

        except Exception as e:
            logger.error(f"Error capturing response tokens: {e}", exc_info=True)
