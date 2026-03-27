from fastapi.testclient import TestClient

from conftest import auth_header

# ── 職務経歴書の削除 ──────────────────────────────────────────


_RESUME_PAYLOAD = {
    "career_summary": "キャリアサマリー",
    "self_pr": "自己PR",
    "experiences": [
        {
            "company": "Example株式会社",
            "business_description": "SES事業",
            "start_date": "2021-04",
            "end_date": "2024-03",
            "is_current": False,
            "employee_count": "300",
            "capital": "10",
            "clients": [
                {
                    "name": "顧客A",
                    "has_client": True,
                    "projects": [
                        {
                            "name": "プロジェクトA",
                            "start_date": "2021-04",
                            "end_date": "2022-03",
                            "is_current": False,
                            "role": "SE",
                            "description": "概要",
                            "challenge": "",
                            "action": "",
                            "result": "",
                            "team": {"total": "5", "members": []},
                            "technology_stacks": [],
                            "phases": [],
                        }
                    ],
                }
            ],
        }
    ],
}


def test_delete_resume_success(client: TestClient) -> None:
    """データがある状態で DELETE → 200、親子テーブルが全て削除されること。"""
    headers = auth_header(client, "del-resume-ok")
    resp = client.post("/api/resumes", json=_RESUME_PAYLOAD, headers=headers)
    assert resp.status_code == 201

    resp = client.delete("/api/resumes", headers=headers)
    assert resp.status_code == 200
    assert "削除しました" in resp.json()["message"]


def test_delete_resume_then_get_404(client: TestClient) -> None:
    """削除後に GET で 404 が返ること。"""
    headers = auth_header(client, "del-resume-get")
    client.post("/api/resumes", json=_RESUME_PAYLOAD, headers=headers)
    client.delete("/api/resumes", headers=headers)

    resp = client.get("/api/resumes/latest", headers=headers)
    assert resp.status_code == 404


def test_delete_resume_not_found(client: TestClient) -> None:
    """データがない状態で DELETE → 404。"""
    headers = auth_header(client, "del-resume-404")
    resp = client.delete("/api/resumes", headers=headers)
    assert resp.status_code == 404


def test_delete_resume_other_user_unaffected(client: TestClient) -> None:
    """他ユーザーのデータが削除されないこと。"""
    headers_a = auth_header(client, "del-resume-a")
    client.post("/api/resumes", json=_RESUME_PAYLOAD, headers=headers_a)

    headers_b = auth_header(client, "del-resume-b")
    client.post("/api/resumes", json=_RESUME_PAYLOAD, headers=headers_b)

    # ユーザーAに切り替えてデータを削除
    headers_a = auth_header(client, "del-resume-a")
    client.delete("/api/resumes", headers=headers_a)

    # ユーザーBに切り替えてデータが残っていることを確認
    headers_b = auth_header(client, "del-resume-b")
    resp = client.get("/api/resumes/latest", headers=headers_b)
    assert resp.status_code == 200


# ── 履歴書の削除 ──────────────────────────────────────────


_RIREKISHO_PAYLOAD = {
    "gender": "male",
    "birthday": "1990-01-15",
    "postal_code": "150-0041",
    "prefecture": "東京都",
    "address": "渋谷区",
    "address_furigana": "しぶやく",
    "email": "test@example.com",
    "phone": "090-1234-5678",
    "motivation": "",
    "personal_preferences": "",
    "photo": None,
    "educations": [{"date": "2010-03", "name": "〇〇大学 卒業"}],
    "work_histories": [{"date": "2010-04", "name": "株式会社〇〇 入社"}],
}


def test_delete_rirekisho_success(client: TestClient) -> None:
    """データがある状態で DELETE → 200、親子テーブルが全て削除されること。"""
    headers = auth_header(client, "del-rirekisho-ok")
    resp = client.post("/api/rirekisho", json=_RIREKISHO_PAYLOAD, headers=headers)
    assert resp.status_code == 201

    resp = client.delete("/api/rirekisho", headers=headers)
    assert resp.status_code == 200
    assert "削除しました" in resp.json()["message"]


def test_delete_rirekisho_then_get_404(client: TestClient) -> None:
    """削除後に GET で 404 が返ること。"""
    headers = auth_header(client, "del-rirekisho-get")
    client.post("/api/rirekisho", json=_RIREKISHO_PAYLOAD, headers=headers)
    client.delete("/api/rirekisho", headers=headers)

    resp = client.get("/api/rirekisho/latest", headers=headers)
    assert resp.status_code == 404


def test_delete_rirekisho_not_found(client: TestClient) -> None:
    """データがない状態で DELETE → 404。"""
    headers = auth_header(client, "del-rirekisho-404")
    resp = client.delete("/api/rirekisho", headers=headers)
    assert resp.status_code == 404


def test_delete_rirekisho_other_user_unaffected(client: TestClient) -> None:
    """他ユーザーのデータが削除されないこと。"""
    headers_a = auth_header(client, "del-rirekisho-a")
    client.post(
        "/api/rirekisho", json=_RIREKISHO_PAYLOAD, headers=headers_a,
    )

    headers_b = auth_header(client, "del-rirekisho-b")
    client.post(
        "/api/rirekisho", json=_RIREKISHO_PAYLOAD, headers=headers_b,
    )

    # ユーザーAに切り替えてデータを削除
    headers_a = auth_header(client, "del-rirekisho-a")
    client.delete("/api/rirekisho", headers=headers_a)

    # ユーザーBに切り替えてデータが残っていることを確認
    headers_b = auth_header(client, "del-rirekisho-b")
    resp = client.get("/api/rirekisho/latest", headers=headers_b)
    assert resp.status_code == 200


def test_delete_resume_can_recreate(client: TestClient) -> None:
    """削除後に再作成できること。"""
    headers = auth_header(client, "del-resume-recreate")
    client.post("/api/resumes", json=_RESUME_PAYLOAD, headers=headers)
    client.delete("/api/resumes", headers=headers)

    resp = client.post("/api/resumes", json=_RESUME_PAYLOAD, headers=headers)
    assert resp.status_code == 201
