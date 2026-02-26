from app.services.pdf_generator import _experience_period, build_resume_pdf, build_Resume_pdf


def test_experience_period_for_current() -> None:
    period = _experience_period("2022-04", None, True)
    assert period == "2022-04 - 在職"


def test_build_resume_pdf_returns_pdf_bytes() -> None:
    payload = {
        "full_name": "山田 太郎",
        "record_date": "2026-02-21",
        "qualifications": [{"acquired_date": "2020-04-01", "name": "応用情報技術者"}],
        "career_summary": "職務要約テスト",
        "self_pr": "自己PRテスト",
        "experiences": [],
    }

    pdf_bytes = build_resume_pdf(payload)

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 100


def test_build_Resume_pdf_returns_pdf_bytes() -> None:
    payload = {
        "full_name": "山田 太郎",
        "record_date": "2026-02-21",
        "qualifications": [{"acquired_date": "2020-04-01", "name": "応用情報技術者"}],
        "postal_code": "150-0001",
        "prefecture": "東京都",
        "address": "渋谷区",
        "email": "test@example.com",
        "phone": "09012345678",
        "motivation": "志望動機テスト",
        "educations": [],
        "work_histories": [],
    }

    pdf_bytes = build_Resume_pdf(payload)

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 100
