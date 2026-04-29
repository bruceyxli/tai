import re
from typing import AsyncIterator, Optional, Set

from app.core.models.chat_completion import DebugInfo, sse
from app.services.generation.base_handler import BaseStreamHandler, StreamContext

# Regex for extracting reference numbers from markdown text
_REFERENCE_PATTERN = re.compile(
    r'(?:\[Reference:\s*([\d,\s]+)\]'
    r'|\breference\s+(\d+(?:(?:\s*,\s*|\s*(?:and|&)\s*)\d+)*))',
    re.IGNORECASE
)


class ChatHandler(BaseStreamHandler):
    """
    Step 3 handler for regular chat mode (TEXT_CHAT_REGULAR + VOICE_REGULAR).

    - Pass-through content transformation (no JSON parsing needed)
    - Regex-based reference extraction: [Reference: 1,2] or 'reference 1'
    - Audio interleaving controlled by audio_response flag (inherited from base)
    """

    def __init__(self, *args, reformulated_query: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.reformulated_query = reformulated_query

    async def run(self) -> AsyncIterator[str]:
        # Emit debug info with reformulated query before streaming
        if self.reformulated_query:
            yield sse(DebugInfo(reformulated_query=self.reformulated_query))
        async for event in super().run():
            yield event

    def transform_delta(self, channel: str, full_text: str, ctx: StreamContext) -> Optional[str]:
        """Identity transform: return raw delta."""
        return full_text[len(ctx.previous_channels.get(channel, "")):]

    def extract_references(self, final_text: str) -> Set[int]:
        """Extract reference numbers using regex pattern matching."""
        return {
            int(n)
            for m in _REFERENCE_PATTERN.finditer(final_text)
            for n in re.findall(r'\d+', m.group(1) or m.group(2))
        }
