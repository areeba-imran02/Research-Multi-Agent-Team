"""Central place for secrets and the Groq language model.

Every other file asks THIS file for the LLM and for API keys,
so secrets are handled in exactly one place.
"""

import inspect
import os
from typing import List, Optional

import streamlit as st
from crewai import LLM

# "groq/" tells CrewAI (through LiteLLM) to use Groq.
# The rest, "openai/gpt-oss-20b", is Groq's own model name.
GROQ_MODEL = "groq/openai/gpt-oss-20b"

# The secrets the app needs.
REQUIRED_SECRETS = ["GROQ_API_KEY"]


# CrewAI (some 1.14+ versions) adds an internal "cache_breakpoint" field to
# messages. It is meant for Anthropic only, and Groq rejects it with a 400 error.
# We remove it before every call to Groq.
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


def _wrap_method(target, method_name: str) -> None:
    """Wrap target.<method_name> so the cache marker is removed first."""
    original = getattr(target, method_name, None)
    if original is None:
        return

    if inspect.iscoroutinefunction(original):
        async def wrapped(*args, **kwargs):
            args, kwargs = _clean_call_arguments(args, kwargs)
            return await original(*args, **kwargs)
    else:
        def wrapped(*args, **kwargs):
            args, kwargs = _clean_call_arguments(args, kwargs)
            return original(*args, **kwargs)

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
    """Read a secret from environment variables or Streamlit secrets.

    Streamlit Community Cloud secrets are available through st.secrets
    (and usually as environment variables too). We check both.
    Returns None if the secret is missing or empty.
    """
    value = os.getenv(name)
    if not value:
        try:
            value = st.secrets.get(name)
        except Exception:
            # No secrets file exists (for example, secrets were never added).
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


def get_llm() -> LLM:
    """Create the Groq language model used by all four agents."""
    api_key = require_secret("GROQ_API_KEY")
    # LiteLLM (used inside CrewAI) reads the key from this environment variable.
    os.environ["GROQ_API_KEY"] = api_key
    llm = LLM(
        model=GROQ_MODEL,
        api_key=api_key,
        temperature=0.2,   # low = more factual, less creative
        max_tokens=6000,   # upper limit for one answer
    )
    # Remove the field that Groq does not accept (see explanation above).
    _wrap_method(llm, "call")
    _wrap_method(llm, "acall")
    _patch_litellm_once()
    return llm
