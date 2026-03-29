import pytest
from fastapi.testclient import TestClient

from conftest import auth_header

# ── CRUD: Auth required (401 without token) ────────────────────


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/api/basic-info"),
        ("get", "/api/basic-info/latest"),
        ("post", "/api/resumes"),
        ("get", "/api/resumes/latest"),
        ("post", "/api/rirekisho"),
        ("get", "/api/rirekisho/latest"),
    ],
)
def test_endpoints_require_auth(client: TestClient, method: str, path: str) -> None:
    resp = getattr(client, method)(path)
    # POST は CSRF チェックが先行して 403、GET は認証チェックで 401 が返る
    assert resp.status_code in (401, 403)


# ── CRUD: Basic Info ────────────────────────────────────────────


def test_basic_info_crud(client: TestClient) -> None:
    headers = auth_header(client, "biuser")

    # Create
    resp = client.post(
        "/api/basic-info",
        json={
            "full_name": "田中太郎",
            "name_furigana": "たなか たろう",
            "record_date": "2026-03-12",
            "qualifications": [{"acquired_date": "2020-04-01", "name": "応用情報技術者"}],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    info_id = resp.json()["id"]

    # Read latest
    resp = client.get("/api/basic-info/latest", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "田中太郎"
    assert resp.json()["qualifications"][0]["name"] == "応用情報技術者"

    # Update
    resp = client.put(
        f"/api/basic-info/{info_id}",
        json={
            "full_name": "田中花子",
            "name_furigana": "たなか はなこ",
            "record_date": "2026-03-12",
            "qualifications": [],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "田中花子"


def test_basic_info_duplicate_create_conflicts(client: TestClient) -> None:
    headers = auth_header(client, "bi-duplicate-user")

    payload = {
        "full_name": "田中太郎",
        "name_furigana": "たなか たろう",
        "record_date": "2026-03-12",
        "qualifications": [],
    }
    assert client.post("/api/basic-info", json=payload, headers=headers).status_code == 201

    resp = client.post("/api/basic-info", json=payload, headers=headers)
    assert resp.status_code == 409


# ── CRUD: Resume ────────────────────────────────────────────────


def test_resume_crud(client: TestClient) -> None:
    headers = auth_header(client, "resumeuser")

    resp = client.post(
        "/api/resumes",
        json={
            "career_summary": "キャリアサマリー",
            "self_pr": "自己PR",
            "experiences": [],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    resume_id = resp.json()["id"]

    resp = client.get("/api/resumes/latest", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["career_summary"] == "キャリアサマリー"

    resp = client.put(
        f"/api/resumes/{resume_id}",
        json={
            "career_summary": "更新済みサマリー",
            "self_pr": "自己PR",
            "experiences": [],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["career_summary"] == "更新済みサマリー"


def test_resume_round_trips_nested_structure(client: TestClient) -> None:
    headers = auth_header(client, "resume-nested-user")

    payload = {
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
                                "name": "API開発",
                                "start_date": "2023-01",
                                "end_date": "2024-03",
                                "is_current": False,
                                "role": "SE",
                                "description": "設計と実装",
                                "challenge": "性能改善",
                                "action": "非同期化",
                                "result": "応答時間短縮",
                                "team": {
                                    "total": "5",
                                    "members": [{"role": "SE", "count": 3}],
                                },
                                "technology_stacks": [
                                    {"category": "language", "name": "Python"},
                                    {"category": "framework", "name": "FastAPI"},
                                ],
                                "phases": ["基本設計", "開発"],
                            }
                        ],
                    }
                ],
            }
        ],
    }

    resp = client.post("/api/resumes", json=payload, headers=headers)
    assert resp.status_code == 201
    resume_id = resp.json()["id"]

    resp = client.get(f"/api/resumes/{resume_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    project = data["experiences"][0]["clients"][0]["projects"][0]
    assert project["name"] == "API開発"
    assert project["team"]["members"][0]["count"] == 3
    assert project["technology_stacks"][1]["name"] == "FastAPI"
    assert project["phases"] == ["基本設計", "開発"]


# ── CRUD: Rirekisho ─────────────────────────────────────────────


def test_rirekisho_crud(client: TestClient) -> None:
    headers = auth_header(client, "rirekishouser")

    resp = client.post(
        "/api/rirekisho",
        json={
            "gender": "male",
            "birthday": "1990-01-15",
            "postal_code": "150-0041",
            "prefecture": "東京都",
            "address": "渋谷区神南1-1-1",
            "address_furigana": "しぶやく じんなん",
            "email": "test@example.com",
            "phone": "09012345678",
            "motivation": "御社の事業に共感しました",
            "educations": [{"date": "2018-03", "name": "○○大学 卒業"}],
            "work_histories": [{"date": "2018-04", "name": "Example株式会社 入社"}],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    rirekisho_id = resp.json()["id"]

    resp = client.get("/api/rirekisho/latest", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["prefecture"] == "東京都"
    assert resp.json()["educations"][0]["date"] == "2018-03"

    resp = client.put(
        f"/api/rirekisho/{rirekisho_id}",
        json={
            "gender": "female",
            "birthday": "1990-01-15",
            "postal_code": "150-0041",
            "prefecture": "東京都",
            "address": "渋谷区神南2-2-2",
            "address_furigana": "しぶやく じんなん",
            "email": "test2@example.com",
            "phone": "09087654321",
            "motivation": "更新済み志望動機",
            "educations": [],
            "work_histories": [],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["gender"] == "female"


def test_rirekisho_duplicate_create_conflicts(client: TestClient) -> None:
    headers = auth_header(client, "rirekisho-duplicate-user")

    payload = {
        "gender": "male",
        "birthday": "1990-01-15",
        "postal_code": "150-0041",
        "prefecture": "東京都",
        "address": "渋谷区神南1-1-1",
        "address_furigana": "しぶやく じんなん",
        "email": "test@example.com",
        "phone": "09012345678",
        "motivation": "",
        "educations": [],
        "work_histories": [],
    }
    assert client.post("/api/rirekisho", json=payload, headers=headers).status_code == 201

    resp = client.post("/api/rirekisho", json=payload, headers=headers)
    assert resp.status_code == 409


# ── Health Check ───────────────────────────────────────────────


def test_health_check(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200


# ── 404: Not Found ─────────────────────────────────────────────


def test_basic_info_not_found(client: TestClient) -> None:
    headers = auth_header(client, "bi404user")
    resp = client.get("/api/basic-info/latest", headers=headers)
    assert resp.status_code == 404


def test_resume_get_by_id(client: TestClient) -> None:
    headers = auth_header(client, "resumegetuser")
    resp = client.post(
        "/api/resumes",
        json={
            "career_summary": "サマリー",
            "self_pr": "自己PR",
            "experiences": [],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    resume_id = resp.json()["id"]

    resp = client.get(f"/api/resumes/{resume_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["career_summary"] == "サマリー"


def test_resume_not_found(client: TestClient) -> None:
    headers = auth_header(client, "resume404user")
    resp = client.get(
        "/api/resumes/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert resp.status_code == 404


def test_rirekisho_get_by_id(client: TestClient) -> None:
    headers = auth_header(client, "ririgetuser")
    resp = client.post(
        "/api/rirekisho",
        json={
            "gender": "male",
            "birthday": "1990-01-15",
            "postal_code": "150-0041",
            "prefecture": "東京都",
            "address": "渋谷区神南1-1-1",
            "address_furigana": "しぶやく じんなん",
            "email": "test@example.com",
            "phone": "09012345678",
            "motivation": "志望動機",
            "educations": [],
            "work_histories": [],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    rirekisho_id = resp.json()["id"]

    resp = client.get(f"/api/rirekisho/{rirekisho_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["prefecture"] == "東京都"


def test_rirekisho_not_found(client: TestClient) -> None:
    headers = auth_header(client, "riri404user")
    resp = client.get(
        "/api/rirekisho/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert resp.status_code == 404
