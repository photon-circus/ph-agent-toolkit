"""Minimal OpenAI-compatible LM Studio chat-completions client."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:1234"


def strip_code_fence(text: str) -> str:
    text = text.strip()
    match = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return match.group(1).strip() if match else text


def call_lm_studio(
    system: str,
    user: str,
    model: str,
    base_url: str | None = None,
    temperature: float = 0.1,
    timeout: float = 300,
) -> dict[str, Any]:
    endpoint = (base_url or os.environ.get("LM_STUDIO_BASE_URL", DEFAULT_BASE_URL)).rstrip(
        "/"
    ) + "/v1/chat/completions"
    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response_data = json.loads(response.read().decode("utf-8"))
    try:
        content = response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("LM Studio response must contain choices[0].message.content") from error
    if not isinstance(content, str):
        raise ValueError("LM Studio response message content must be a string")
    parsed = json.loads(strip_code_fence(content))
    if not isinstance(parsed, dict):
        raise ValueError("LM Studio response content must be a JSON object")
    return parsed
