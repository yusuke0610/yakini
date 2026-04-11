import base64

from app.services.pdf.generators.resume_generator import build_resume_pdf
from app.services.pdf.utils.pdf_utils import (
    decode_photo as _decode_photo,
)
from app.services.pdf.utils.pdf_utils import (
    format_period as _format_period,
)
from app.services.pdf.utils.pdf_utils import (
    parse_date_ym as _parse_date_ym,
)


def test_format_period_for_current() -> None:
    period = _format_period("2022-04", None, True)
    assert "現在" in period


def test_build_resume_pdf_returns_pdf_bytes() -> None:
    payload = {
        "full_name": "山田 太郎",
        "qualifications": [{"acquired_date": "2020-04-01", "name": "応用情報技術者"}],
        "career_summary": "職務要約テスト",
        "self_pr": "自己PRテスト",
        "experiences": [],
    }

    pdf_bytes = build_resume_pdf(payload)

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 100


def test_parse_date_ym() -> None:
    assert _parse_date_ym("2020-04") == ("2020", "4")
    assert _parse_date_ym("2020-12-01") == ("2020", "12")
    assert _parse_date_ym("") == ("", "")
    assert _parse_date_ym("invalid") == ("", "")


def test_decode_photo_valid() -> None:
    # 1x1 red PNG
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
        b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
        b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode()
    result = _decode_photo(data_url)
    assert result is not None
    assert result.read()[:4] == b"\x89PNG"


def test_decode_photo_none() -> None:
    assert _decode_photo(None) is None
    assert _decode_photo("") is None
    assert _decode_photo("not-a-data-url") is None
