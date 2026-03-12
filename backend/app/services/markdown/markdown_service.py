from typing import Any

from .generators.resume_generator import build_resume_markdown
from .generators.rirekisho_generator import build_rirekisho_markdown


def generate_resume_markdown(payload: dict[str, Any]) -> str:
    return build_resume_markdown(payload)


def generate_rirekisho_markdown(payload: dict[str, Any]) -> str:
    return build_rirekisho_markdown(payload)
