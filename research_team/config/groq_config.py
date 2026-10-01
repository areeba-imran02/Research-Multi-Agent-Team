"""Central place for secrets and the Groq language model.

Every other file asks THIS file for the LLM and for API keys,
so secrets are handled in exactly one place.
"""

import asyncio
import inspect
import os
import re
import time
from typing import Callable, List, Optional

import streamlit as st
from crewai import LLM

# "groq/" tells CrewAI (through LiteLLM) to use Groq.
GROQ_MODEL = "groq/openai/gpt-oss-20b"

# The secrets the app needs.
REQUIRED_SECRETS = ["GROQ_API_KEY"]

# ---------------------------------------------------------------------------
# Rate-limit handling (Groq free plan has a small tokens-per-minute limit).
# When Groq says "try again in 8s", we wait and repeat only that ONE call,
# so the whole research run does not have to start again.
# ---------------------------------------------------------------------------
MAX_RATE_RETRIES = 8
MAX_WAIT_SECONDS = 90

_wait_notifier: Optional[Callable[[int], None]] = None


def set_wait_notifier(callback: Optional[Callable[[int], None]]) -> None:
    """Let the screen show 'waiting N seconds' while we pause for the rate limit."""
    global _wait_notifier
    _wait_notifier = callback


def _notify(seconds: int) -> None:
    if _wait_notifier:
        try:
            _wait_notifier(seconds)
        except Exception:
            pass


def _parse_wait_seconds(text: str) -> Optional[float]:
    """Read 'try again in 7.5s' / '1m12.5s' / '340ms' from a Groq error message."""
    match = re.search(r"try again in ([0-9.hms]+)", text)
    if not match:
        return None
    total = 0.0
    found = False
    for number, unit in re.findall(r"(\d+(?:\.\d+)?)(ms|h|m|s)", match.group(1)):
        found = True
        value = float(number)
        total += {"ms": value / 1000, "s": value, "m": value * 60, "h": value * 3600}[unit]
    return total if found else None


def _retry_delay(exc: Exception, attempt: int) -> Optional[float]:
    """How long to wait before retrying, or None if we should not retry."""
    if attempt >= MAX_RATE_RETRIES:
        return None
    text = str(exc).lower()
    name = type(exc).__name__.lower()
    if "request too large" in text or "413" in text:
        return None  # waiting will not help: the single request is too big
    if not ("ratelimit" in name or "rate limit" in text or "rate_limit" in text or "429" in text):
        return None
    wait = _parse_wait_seconds(text)
    if wait is None:
        wait = 15 * (attempt + 1)
    wait = wait + 1.5
    if wait > MAX_WAIT_SECONDS:
        return None  # probably the daily limit
    return wait


def _sleep_with_countdown(seconds: float) -> None:
    remaining = int(seconds + 0.5)
    while remaining > 0:
        _notify(remaining)
        time.sleep(1)
        remaining -= 1
    _notify(0)


# ---------------------------------------------------------------------------
# Groq does not accept CrewAI's internal "cache_breakpoint" message field.
# We remove it before every call.
# ---------------------------------------------------------------------------
CACHE_MARKER = "cache_breakpoint"


def strip_cache_marker(messages):
    """Return a copy of the messages without the 'cache_breakpoint' field."""
    if not isinstance(messages, list):
        return messages
    cleaned = []
    for message in messages:
        if isinstance(message, dict) and CACHE_MARKER in message:
            message = {key: value for key, value in message.items() if key != CACHE_MARKER}
        cleaned.append(message)
    return cleaned


def _clean_call_arguments(args: tuple, kwargs: dict):
    """Clean the 'messages' argument, whether it is positional or a keyword."""
    if args:
        args = (strip_cache_marker(args[0]),) + tuple(args[1:])
    elif "messages" in kwargs:
        kwargs = dict(kwargs)
        kwargs["messages"] = strip_cache_marker(kwargs["messages"])
    return args, kwargs


def _wrap_method(target, method_name: str, retry: bool = False) -> None:
    """Wrap target.<method_name>: remove the cache marker and (optionally) retry on rate limit."""
    original = getattr(target, method_name, None)
    if original is None:
        return

    if inspect.iscoroutinefunction(original):
        async def wrapped(*args, **kwargs):
            args, kwargs = _clean_call_arguments(args, kwargs)
            attempt = 0
            while True:
                try:
                    return await original(*args, **kwargs)
                except Exception as exc:
                    delay = _retry_delay(exc, attempt) if retry else None
                    if delay is None:
                        raise
                    attempt += 1
                    await asyncio.sleep(delay)
    else:
        def wrapped(*args, **kwargs):
            args, kwargs = _clean_call_arguments(args, kwargs)
            attempt = 0
            while True:
                try:
                    return original(*args, **kwargs)
                except Exception as exc:
                    delay = _retry_delay(exc, attempt) if retry else None
                    if delay is None:
                        raise
                    attempt += 1
                    _sleep_with_countdown(delay)

    try:
        setattr(target, method_name, wrapped)
    except Exception:
        object.__setattr__(target, method_name, wrapped)


def _patch_litellm_once() -> None:
    """Second safety net: also clean messages right before LiteLLM sends them."""
    try:
        import litellm
    except ImportError:
        return
    if getattr(litellm, "_cache_marker_patched", False):
        return
    for name in ("completion", "acompletion"):
        _wrap_method(litellm, name)
    litellm._cache_marker_patched = True


class ConfigError(Exception):
    """Raised when something is wrong with the app configuration."""


def get_secret(name: str) -> Optional[str]:
    """Read a secret from environment variables or Streamlit secrets."""
    value = os.getenv(name)
    if not value:
        try:
            value = st.secrets.get(name)
        except Exception:
            value = None
    if value:
        return str(value).strip()
    return None


def missing_secrets() -> List[str]:
    """Return the names of required secrets that are not set."""
    return [name for name in REQUIRED_SECRETS if not get_secret(name)]


def require_secret(name: str) -> str:
    """Return a secret, or raise a clean error if it is missing."""
    value = get_secret(name)
    if not value:
        raise ConfigError(f"The secret {name} is missing. Please add it in the app settings.")
    return value


def redact(text: str) -> str:
    """Remove any secret values from text so they never reach the screen or logs."""
    for name in REQUIRED_SECRETS:
        value = get_secret(name)
        if value:
            text = text.replace(value, "[hidden]")
    return text


def get_llm(max_tokens: int = 1500) -> LLM:
    """Create the Groq language model.

    max_tokens is kept small on purpose: the free Groq plan counts it
    against the tokens-per-minute limit. gpt-oss is a reasoning model, so
    do not go below ~1500 or answers may be cut short.
    """
    api_key = require_secret("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = api_key  # LiteLLM reads the key from here

    model_name = get_secret("GROQ_MODEL") or GROQ_MODEL
    options = {}
    # Low reasoning effort = fewer hidden tokens = fits the free limit.
    # Set the secret GROQ_REASONING to "off" to disable this option.
    effort = (get_secret("GROQ_REASONING") or "low").lower()
    if "gpt-oss" in model_name and effort in ("low", "medium", "high"):
        options["reasoning_effort"] = effort

    llm = LLM(
        model=model_name,
        api_key=api_key,
        temperature=0.2,
        max_tokens=max_tokens,
        **options,
    )
    _wrap_method(llm, "call", retry=True)
    _wrap_method(llm, "acall", retry=True)
    _patch_litellm_once()
    return llm
