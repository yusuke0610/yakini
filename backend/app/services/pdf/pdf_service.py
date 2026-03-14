from .generators.intelligence_generator import build_intelligence_pdf
from .generators.resume_generator import build_resume_pdf
from .generators.rirekisho_generator import build_rirekisho_pdf


def generate_resume(resume: dict) -> bytes:
    return build_resume_pdf(resume)


def generate_rirekisho(rirekisho: dict) -> bytes:
    return build_rirekisho_pdf(rirekisho)


def generate_intelligence_report(payload: dict) -> bytes:
    return build_intelligence_pdf(payload)
