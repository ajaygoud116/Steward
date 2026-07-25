import os
import json
from pathlib import Path
from lyzr import Studio

_raw_agent_cache = {}
_wrapped_agent_cache = {}
_PROMPTS_DIR = Path(__file__).parent / "prompts"


def get_agent(studio: Studio, response_model=None):
    agent_id = os.getenv("Mission_Manager_AGENT_ID")
    if not agent_id:
        raise RuntimeError("Mission_Manager_AGENT_ID not set in .env. Create the agent in Studio first.")

    if response_model:
        if agent_id in _wrapped_agent_cache:
            return _wrapped_agent_cache[agent_id]
        raw_agent = _get_raw_agent(studio, agent_id)
        wrapped = _StructuredAgent(raw_agent, response_model)
        _wrapped_agent_cache[agent_id] = wrapped
        return wrapped

    return _get_raw_agent(studio, agent_id)


def _get_raw_agent(studio, agent_id):
    if agent_id in _raw_agent_cache:
        return _raw_agent_cache[agent_id]
    agent = studio.get_agent(agent_id)
    _raw_agent_cache[agent_id] = agent
    return agent


def run_mode(studio: Studio, mode: str, context: dict, response_model):
    """Load a prompt template, format with context, call the agent, parse JSON into response_model."""
    prompt_file = _PROMPTS_DIR / f"{mode}.md"
    if not prompt_file.exists():
        raise ValueError(f"Unknown mode '{mode}'. No prompt file found at {prompt_file}")

    template = prompt_file.read_text(encoding="utf-8")
    message = template
    for key, value in context.items():
        message = message.replace(f"{{{key}}}", str(value))

    agent = get_agent(studio)
    result = agent.run(message)

    raw = result.response
    data = _extract_json(raw)
    try:
        return response_model(**data)
    except (TypeError, ValueError) as e:
        raise RuntimeError(f"Failed to parse {mode} response as {response_model.__name__}: {e}") from e


def _extract_json(text: str) -> dict:
    """Extract JSON from text that may contain markdown code blocks or wrapper text."""
    text = text.strip()
    # Remove markdown code block fences
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    # Try parsing directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
        return json.loads(text)
    raise ValueError(f"No valid JSON found in response: {text[:200]}")


class _StructuredAgent:
    """Wraps a Lyzr Agent to parse structured JSON output into a Pydantic model."""

    def __init__(self, agent, response_model):
        self._agent = agent
        self._response_model = response_model

    def run(self, *args, **kwargs):
        result = self._agent.run(*args, **kwargs)
        try:
            data = _extract_json(result.response)
            return self._response_model(**data)
        except (ValueError, TypeError):
            return result
