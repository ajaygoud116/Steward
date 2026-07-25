import re
from typing import List
from pydantic import BaseModel


class GuardrailResult(BaseModel):
    passed: bool
    flags: List[str]
    categories: List[str] = []


_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|directions|prompts|rules)",
    r"forget\s+(all\s+)?(previous|prior)\s+(instructions|directions|prompts|rules)",
    r"disregard\s+(all\s+)?(previous|prior)\s+(instructions|directions|prompts|rules)",
    r"you\s+are\s+now\s+",
    r"new\s+(instructions|directions|prompts|rules|system prompt)",
    r"override\s+(instructions|directions|prompts|rules)",
    r"system\s+prompt",
    r"you\s+must\s+ignore",
    r"do\s+not\s+follow",
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+(if\s+)?",
    r"simulate\s+(being|a)",
    r"you\s+are\s+free\s+to",
    r"no\s+(rules|boundaries|restrictions|limitations)",
]

_PII_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "email"),
    (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "phone"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "ssn"),
    (r"\b(?:\d[ -]*?){13,19}\b", "credit_card"),
    (r"\b(?:US\s+)?\$\d+(?:,\d{3})*(?:\.\d{2})?\b", "financial"),
]

_TOXIC_WORDS = [
    "hate", "kill", "destroy", "attack", "bomb", "terrorist",
    "stupid", "idiot", "useless", "worthless",
    "die", "murder", "suicide", "harm",
]


class RAIGuardrails:
    """Deterministic Responsible AI guardrails: injection, PII, toxicity."""

    @staticmethod
    def check_input(text: str) -> GuardrailResult:
        flags: List[str] = []
        categories: List[str] = []
        lower = text.lower()

        for pattern in _INJECTION_PATTERNS:
            if re.search(pattern, lower):
                flags.append(f"Prompt injection: matched pattern '{pattern}'")
                categories.append("injection")
                break

        for pattern, label in _PII_PATTERNS:
            if re.search(pattern, text):
                flags.append(f"PII detected: {label}")
                categories.append("pii")

        for word in _TOXIC_WORDS:
            if word in lower.split():
                flags.append(f"Toxic content: contains '{word}'")
                categories.append("toxicity")

        return GuardrailResult(
            passed=len(flags) == 0,
            flags=flags,
            categories=list(set(categories)),
        )

    @staticmethod
    def check_output(text: str) -> GuardrailResult:
        flags: List[str] = []
        categories: List[str] = []
        lower = text.lower()

        for pattern, label in _PII_PATTERNS:
            if re.search(pattern, text):
                flags.append(f"PII detected in output: {label}")
                categories.append("pii")

        for word in _TOXIC_WORDS:
            if word in lower.split():
                flags.append(f"Toxic content in output: '{word}'")
                categories.append("toxicity")

        return GuardrailResult(
            passed=len(flags) == 0,
            flags=flags,
            categories=list(set(categories)),
        )
