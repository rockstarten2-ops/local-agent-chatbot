"""Helpers for extracting text from OpenAI-compatible chat responses."""

from __future__ import annotations

from typing import Any, Dict, List


def _join_content_blocks(blocks: List[Any]) -> str:
    """Join text-like content blocks into a single string."""
    text_parts: List[str] = []
    for block in blocks:
        if isinstance(block, str):
            if block.strip():
                text_parts.append(block.strip())
            continue

        if not isinstance(block, dict):
            continue

        block_text = block.get("text")
        if isinstance(block_text, str) and block_text.strip():
            text_parts.append(block_text.strip())
            continue

        if block.get("type") == "thinking":
            thinking_text = block.get("thinking")
            if isinstance(thinking_text, str) and thinking_text.strip():
                text_parts.append(thinking_text.strip())

    return "\n".join(text_parts).strip()


def extract_chat_completion_text(response_json: Dict[str, Any]) -> str:
    """Extract answer text from chat completion payload with robust fallbacks."""
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing or empty 'choices' in LLM response.")

    first_choice = choices[0] if isinstance(choices[0], dict) else {}
    message = first_choice.get("message") if isinstance(first_choice.get("message"), dict) else {}

    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        joined = _join_content_blocks(content)
        if joined:
            return joined

    reasoning_content = message.get("reasoning_content")
    if isinstance(reasoning_content, str) and reasoning_content.strip():
        return reasoning_content.strip()
    if isinstance(reasoning_content, list):
        joined_reasoning = _join_content_blocks(reasoning_content)
        if joined_reasoning:
            return joined_reasoning

    fallback_text = first_choice.get("text")
    if isinstance(fallback_text, str) and fallback_text.strip():
        return fallback_text.strip()

    raise ValueError(
        "No usable answer text found in LLM response. "
        f"Top-level keys: {list(response_json.keys())}"
    )
