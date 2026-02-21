import pytest
from pydantic import ValidationError

from app.schemas import Experience, ResumeCreate


def experience_payload() -> dict:
    return {
        "company": "Example株式会社",
        "title": "バックエンドエンジニア",
        "start_date": "2021-04",
        "end_date": "2024-03",
        "is_current": False,
        "description": "API開発",
        "achievements": "処理速度を改善",
        "employee_count": "300名",
        "capital": "1億円",
        "technology_stacks": [{"category": "言語", "name": "Python"}],
    }


def test_current_experience_forces_end_date_none() -> None:
    payload = experience_payload()
    payload["is_current"] = True
    payload["end_date"] = "2024-03"

    experience = Experience(**payload)

    assert experience.end_date is None


def test_end_date_is_required_when_not_current() -> None:
    payload = experience_payload()
    payload["is_current"] = False
    payload["end_date"] = ""

    with pytest.raises(ValidationError):
        Experience(**payload)


def test_framework_category_is_accepted() -> None:
    payload = experience_payload()
    payload["technology_stacks"] = [{"category": "フレームワーク", "name": "FastAPI"}]

    experience = Experience(**payload)

    assert experience.technology_stacks[0].category == "フレームワーク"


def test_unknown_category_is_rejected() -> None:
    payload = experience_payload()
    payload["technology_stacks"] = [{"category": "ミドルウェア", "name": "Nginx"}]

    with pytest.raises(ValidationError):
        Experience(**payload)


def test_resume_requires_career_summary() -> None:
    payload = {
        "self_pr": "自己PR",
        "experiences": [experience_payload()],
    }

    with pytest.raises(ValidationError):
        ResumeCreate(**payload)
