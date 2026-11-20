"""Optional API clients for *actual* commercial LLM evaluation.

Transport-only. No actions are performed on a model's instructions. By default
all provider calls are disabled unless the operator supplies an API key and
explicitly executes the live CLI. Uses fixed HTTPS origins and bounded bodies.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

MAX_OUTPUT_BYTES = 1_048_576
MAX_PROMPT_BYTES = 80_000
MODEL_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")

class ProviderError(RuntimeError):
    """Safe error: deliberately excludes response bodies and credentials."""

@dataclass(frozen=True)
class ModelReply:
    provider: str
    model: str
    text: str
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None


def _post(url: str, payload: dict, headers: dict, timeout: int = 45) -> dict:
    if type(timeout) is not int or not 1 <= timeout <= 120:
        raise ProviderError('Invalid timeout')
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    if len(data) > MAX_PROMPT_BYTES:
        raise ProviderError('Request too large')
    request = Request(url, data=data, headers={"Content-Type": "application/json", **headers}, method='POST')
    class DenyRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    try:
        # Never forward API keys to a redirect target, including cross-origin.
        with build_opener(DenyRedirect).open(request, timeout=timeout) as response:
            size_hint = response.headers.get('Content-Length')
            if size_hint and int(size_hint) > MAX_OUTPUT_BYTES:
                raise ProviderError('Provider response too large')
            raw = response.read(MAX_OUTPUT_BYTES + 1)
    except HTTPError as exc:
        raise ProviderError(f'Provider returned HTTP {exc.code}; inspect provider logs') from None
    except URLError:
        raise ProviderError('Provider connection error') from None
    if len(raw) > MAX_OUTPUT_BYTES:
        raise ProviderError('Provider response too large')
    try:
        result = json.loads(raw.decode('utf-8'))
        if not isinstance(result, dict):
            raise ValueError('not an object')
        return result
    except (UnicodeError, ValueError) as exc:
        raise ProviderError('Invalid provider response') from exc


def ask_model(provider: str, model: str, prompt: str, *, api_key: str | None = None,
              timeout: int = 45) -> ModelReply:
    """Call OpenAI Responses, Anthropic Messages or Gemini generateContent.

    No API requests are issued without credentials. This may incur charges.
    Model identifiers are single path segments, not caller-controlled URLs.
    """
    if provider not in ('openai', 'anthropic', 'gemini'):
        raise ProviderError('Unsupported provider')
    if not isinstance(model, str) or not MODEL_ID.fullmatch(model):
        raise ProviderError('Invalid model ID')
    if not isinstance(prompt, str) or not prompt or len(prompt.encode('utf-8')) > MAX_PROMPT_BYTES - 2500:
        raise ProviderError('Invalid or oversized prompt')
    env_name = {'openai': 'OPENAI_API_KEY', 'anthropic': 'ANTHROPIC_API_KEY', 'gemini': 'GEMINI_API_KEY'}[provider]
    key = api_key if api_key is not None else os.environ.get(env_name)
    if not isinstance(key, str) or not key.strip() or '\n' in key or '\r' in key:
        raise ProviderError(f'API credentials missing or invalid: configure {env_name}')
    if provider == 'openai':
        url = 'https://api.openai.com/v1/responses'
        headers = {'Authorization': f'Bearer {key}'}
        payload = {'model': model, 'input': prompt, 'max_output_tokens': 400, 'store': False}
    elif provider == 'anthropic':
        url = 'https://api.anthropic.com/v1/messages'
        headers = {'x-api-key': key, 'anthropic-version': '2023-06-01'}
        payload = {'model': model, 'max_tokens': 400, 'messages': [{'role': 'user', 'content': prompt}]}
    else:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        headers = {'x-goog-api-key': key}
        payload = {'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {'maxOutputTokens': 400}}
    started = time.perf_counter_ns()
    result = _post(url, payload, headers, timeout)
    ms = max(0, round((time.perf_counter_ns()-started)/1_000_000))
    try:
        if provider == 'openai':
            parts = [part['text'] for item in result['output'] if item.get('type') == 'message'
                     for part in item['content'] if part.get('type') == 'output_text']
            usage = result.get('usage') or {}
            i, o = usage.get('input_tokens'), usage.get('output_tokens')
        elif provider == 'anthropic':
            parts = [part['text'] for part in result['content'] if part.get('type') == 'text']
            usage = result.get('usage') or {}
            i, o = usage.get('input_tokens'), usage.get('output_tokens')
        else:
            parts = [p['text'] for p in result['candidates'][0]['content']['parts'] if 'text' in p]
            usage = result.get('usageMetadata') or {}
            i, o = usage.get('promptTokenCount'), usage.get('candidatesTokenCount')
        text = '\n'.join(parts)
        if not text or len(text.encode('utf-8')) > MAX_OUTPUT_BYTES:
            raise ValueError('empty or oversized text')
        return ModelReply(provider, model, text, ms,
                          i if type(i) is int and i >= 0 else None,
                          o if type(o) is int and o >= 0 else None)
    except (KeyError, IndexError, TypeError, ValueError):
        raise ProviderError('Incomplete or unsupported provider response') from None
