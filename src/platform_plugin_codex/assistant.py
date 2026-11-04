"""OpenAI's Responses API through the contract's client (liminal_lib.assistants.ResponsesAssistant),
as OpenAI documents it at https://developers.openai.com/api/docs (verified 2026-11-03): POST
/v1/responses with `instructions`, `input`, `max_output_tokens` (16 at least), `store` false,
`safety_identifier` (a digest of the account: the field takes no identifying information),
`reasoning.effort` where set; the answer's `output[]` message items; `usage` with the cached and
reasoning details; the errors' `{error: {message, type, code, param}}` shape; the x-ratelimit-*
headers, from which Connect reads the usage tier."""
from __future__ import annotations

from liminal_lib.assistants import ResponsesAssistant

API = "https://api.openai.com"


class CodexAssistant(ResponsesAssistant):
    """Codex: the Responses API at api.openai.com with a bearer key and the account's digest as the
    safety identifier; everything else is the Responses API's shape (ResponsesAssistant)."""

    base_url = API
    user_field = "safety_identifier"
    limit_prefixes = ("x-ratelimit-",)
