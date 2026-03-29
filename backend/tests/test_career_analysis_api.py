from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from conftest import auth_header


def _create_resume(client: TestClient, headers: dict[str, str]) -> None:
    resp = client.post(
        "/api/resumes",
        json={
            "career_summary": "バックエンド中心の開発経験",
            "self_pr": "API 設計が得意",
            "experiences": [],
        },
        headers=headers,
    )
    assert resp.status_code == 201


def test_generate_returns_specific_error_when_llm_is_unavailable(client: TestClient) -> None:
    headers = auth_header(client, "career-llm-off")
    _create_resume(client, headers)

    with patch(
        "app.routers.career_analysis._llm_client.check_available",
        new=AsyncMock(return_value=False),
    ):
        resp = client.post(
            "/api/career-analysis/generate",
            json={"target_position": "Backend Engineer"},
            headers=headers,
        )

    assert resp.status_code == 503
    assert (
        resp.json()["detail"]
        == "AI キャリアパス分析サービスが利用できません。LLM の設定または接続状態を確認してください。"
    )


def test_generate_returns_specific_error_when_llm_response_is_empty(client: TestClient) -> None:
    headers = auth_header(client, "career-llm-empty")
    _create_resume(client, headers)

    with (
        patch(
            "app.routers.career_analysis._llm_client.check_available",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.routers.career_analysis.build_career_analysis",
            new=AsyncMock(side_effect=ValueError("LLM からの応答が空です")),
        ),
    ):
        resp = client.post(
            "/api/career-analysis/generate",
            json={"target_position": "Backend Engineer"},
            headers=headers,
        )

    assert resp.status_code == 503
    assert (
        resp.json()["detail"]
        == "AI キャリアパス分析サービスが利用できません。LLM の設定または接続状態を確認してください。"
    )
