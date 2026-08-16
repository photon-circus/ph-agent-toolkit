"""Minimal OpenAI-compatible LM Studio client."""

from __future__ import annotations

import json
import math
import os
import re
import urllib.request
from typing import Any
from urllib.parse import urlsplit

DEFAULT_BASE_URL = "http://127.0.0.1:1234"
MAX_RESPONSE_BYTES = 262_144
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


def _strip_fence(text: str) -> str:
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text.strip(), re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()


def call_lm_studio(
    system: str,
    user: str,
    model: str,
    *,
    base_url: str | None = None,
    temperature: float = 0.1,
    timeout: float = 300,
) -> dict[str, Any]:
    if not math.isfinite(temperature) or not 0 <= temperature <= 2:
        raise ValueError("temperature must be finite and between 0 and 2")
    if not math.isfinite(timeout) or not 0 < timeout <= 600:
        raise ValueError("timeout must be finite and no greater than 600 seconds")
    configured = (base_url or os.environ.get("LM_STUDIO_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
    parsed_url = urlsplit(configured)
    if (
        parsed_url.scheme != "http"
        or parsed_url.hostname not in _LOOPBACK_HOSTS
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.query
        or parsed_url.fragment
        or parsed_url.path not in {"", "/"}
    ):
        raise ValueError("LM Studio base URL must be an uncredentialed loopback HTTP origin")
    endpoint = configured
    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    request = urllib.request.Request(
        endpoint + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw_response = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw_response) > MAX_RESPONSE_BYTES:
        raise ValueError(f"LM Studio response exceeds {MAX_RESPONSE_BYTES} bytes")
    response_data = json.loads(raw_response.decode("utf-8"))
    try:
        content = response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("LM Studio response must contain choices[0].message.content") from error
    if not isinstance(content, str):
        raise ValueError("LM Studio response content must be a string")
    parsed = json.loads(_strip_fence(content))
    if not isinstance(parsed, dict):
        raise ValueError("LM Studio response content must be a JSON object")
    return parsed
