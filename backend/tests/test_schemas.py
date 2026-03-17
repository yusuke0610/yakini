import pytest
from pydantic import ValidationError

from app.schemas import Experience, ResumeCreate, RirekishoCreate


def experience_payload() -> dict:
    return {
        "company": "Example株式会社",
        "business_description": "SES事業",
        "start_date": "2021-04",
        "end_date": "2024-03",
        "is_current": False,
        "employee_count": "300名",
        "capital": "1億円",
        "clients": [
            {
                "name": "クライアントA",
                "projects": [
                    {
                        "name": "API開発",
                        "role": "メンバー",
                        "description": "API開発",
                        "achievements": "処理速度を改善",
                        "scale": "5名",
                        "technology_stacks": [{"category": "language", "name": "Python"}],
                    }
                ],
            }
        ],
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
    payload["clients"][0]["projects"][0]["technology_stacks"] = [
        {"category": "framework", "name": "FastAPI"}
    ]

    experience = Experience(**payload)

    assert experience.clients[0].projects[0].technology_stacks[0].category == "framework"


def test_unknown_category_is_rejected() -> None:
    payload = experience_payload()
    payload["clients"][0]["projects"][0]["technology_stacks"] = [
        {"category": "ミドルウェア", "name": "Nginx"}
    ]

    with pytest.raises(ValidationError):
        Experience(**payload)


def test_resume_requires_career_summary() -> None:
    payload = {
        "self_pr": "自己PR",
        "experiences": [experience_payload()],
    }

    with pytest.raises(ValidationError):
        ResumeCreate(**payload)


def rirekisho_payload() -> dict:
    return {
        "name_furigana": "やまだ たろう",
        "gender": "male",
        "prefecture": "東京都",
        "address": "渋谷区神南1-1-1",
        "address_furigana": "しぶやく じんなん",
        "email": "test@example.com",
        "phone": "09012345678",
        "motivation": "御社の事業に共感しました",
        "educations": [{"date": "2018-03", "name": "○○大学 卒業"}],
        "work_histories": [{"date": "2018-04", "name": "Example株式会社 入社"}],
    }


def test_rirekisho_create_valid() -> None:
    rirekisho = RirekishoCreate(**rirekisho_payload())

    assert rirekisho.name_furigana == "やまだ たろう"
    assert rirekisho.gender == "male"
    assert len(rirekisho.educations) == 1
    assert len(rirekisho.work_histories) == 1


def test_rirekisho_requires_prefecture() -> None:
    payload = rirekisho_payload()
    del payload["prefecture"]

    with pytest.raises(ValidationError):
        RirekishoCreate(**payload)


def test_rirekisho_allows_empty_motivation() -> None:
    payload = rirekisho_payload()
    payload["motivation"] = ""

    rirekisho = RirekishoCreate(**payload)
    assert rirekisho.motivation == ""
