"""One OpenRouter chat client. Stdlib only. Reads OPENROUTER_API_KEY via envkeys.

Used for LLM cleanup of OCR/converter output AND (via core.vision) for image OCR, on
OPEN-WEIGHTS models (Qwen/Gemma/Mistral) which — unlike proprietary APIs — do NOT block
verbatim reproduction of copyrighted text. So full-text cleanup of the user's own
material works without the `Output blocked by content filtering policy` wall.

Do NOT default to proprietary models (openai/*, anthropic/*, google/gemini-*) for
verbatim reproduction of copyrighted material — they carry moderation and re-introduce
the block. (The catalog flags this as `is_moderated: true`.)
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from .envkeys import resolve as resolve_key

URL = "https://openrouter.ai/api/v1/chat/completions"
# Open-weight default for FIX-ONLY cleanup. Chosen by bake-off (see references/models.md):
# gemma-4-31b-it matched qwen3.6-35b/27b at 99% word-fidelity on the cleanup task while being the
# cheapest, and it's the same model the vision path uses — one model, moderated:false, pt-BR + EN.
DEFAULT_MODEL = "google/gemma-4-31b-it"

_RETRY_CODES = {408, 429, 500, 502, 503, 520, 524, 529}


class OpenRouterError(RuntimeError):
    """Raised on unrecoverable OpenRouter API failures."""


def chat(messages: list[dict], model: str = DEFAULT_MODEL, temperature: float = 0.0,
         max_tokens: int = 16384, max_retries: int = 5, timeout: int = 240,
         key: str | None = None) -> str:
    """POST a chat completion; return the assistant text. Retries transient errors.

    `messages` may contain multimodal content parts (text + image_url) — the caller
    (e.g. core.vision) builds them; this client just serializes and posts.

    `max_tokens` is bounded (not the model's full context) so OpenRouter's balance gate
    ("must afford the max") doesn't reject the request. Callers with big chunks raise it.
    """
    key = key or resolve_key("OPENROUTER_API_KEY")
    if not key:
        raise OpenRouterError("OPENROUTER_API_KEY not set (env or scripts/.env)")

    payload = json.dumps({
        "model": model, "temperature": temperature,
        "max_tokens": max_tokens, "messages": messages,
    }).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "X-Title": "axi25-source",
    }
    delay = 2.0
    for attempt in range(max_retries):
        req = urllib.request.Request(URL, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.load(resp)
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            if e.code in _RETRY_CODES and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise OpenRouterError(f"HTTP {e.code}: {body}")
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise OpenRouterError(str(e))
    raise OpenRouterError("exhausted retries")
