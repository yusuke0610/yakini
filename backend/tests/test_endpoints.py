import pytest
from fastapi.testclient import TestClient

from conftest import auth_header


# ── Auth: Register ──────────────────────────────────────────────


def test_register_success(client: TestClient) -> None:
    resp = client.post("/auth/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "SecurePass123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "username" in data
    assert data["username"] == "alice"


def test_register_duplicate_username(client: TestClient) -> None:
    payload = {"username": "bob", "email": "bob@example.com", "password": "SecurePass123"}
    client.post("/auth/register", json=payload)

    resp = client.post("/auth/register", json={
        "username": "bob",
        "email": "bob2@example.com",
        "password": "SecurePass123",
    })
    assert resp.status_code == 409


def test_register_duplicate_email(client: TestClient) -> None:
    payload = {"username": "carol", "email": "carol@example.com", "password": "SecurePass123"}
    client.post("/auth/register", json=payload)

    resp = client.post("/auth/register", json={
        "username": "carol2",
        "email": "carol@example.com",
        "password": "SecurePass123",
    })
    assert resp.status_code == 409


def test_register_short_password(client: TestClient) -> None:
    resp = client.post("/auth/register", json={
        "username": "dave",
        "email": "dave@example.com",
        "password": "short",
    })
    assert resp.status_code == 422


def test_register_invalid_email(client: TestClient) -> None:
    resp = client.post("/auth/register", json={
        "username": "eve",
        "email": "not-an-email",
        "password": "SecurePass123",
    })
    assert resp.status_code == 422


# ── Auth: Login ─────────────────────────────────────────────────


def test_login_success(client: TestClient) -> None:
    client.post("/auth/register", json={
        "username": "frank",
        "email": "frank@example.com",
        "password": "SecurePass123",
    })

    resp = client.post("/auth/login", json={
        "email": "frank@example.com",
        "password": "SecurePass123",
    })
    assert resp.status_code == 200
    assert "username" in resp.json()


def test_login_wrong_password(client: TestClient) -> None:
    client.post("/auth/register", json={
        "username": "grace",
        "email": "grace@example.com",
        "password": "SecurePass123",
    })

    resp = client.post("/auth/login", json={
        "email": "grace@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_login_nonexistent_user(client: TestClient) -> None:
    resp = client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "SecurePass123",
    })
    assert resp.status_code == 401


# ── CRUD: Auth required (401 without token) ────────────────────


@pytest.mark.parametrize("method,path", [
    ("post", "/api/basic-info"),
    ("get", "/api/basic-info/latest"),
    ("post", "/api/resumes"),
    ("get", "/api/resumes/latest"),
    ("post", "/api/rirekisho"),
    ("get", "/api/rirekisho/latest"),
])
def test_endpoints_require_auth(client: TestClient, method: str, path: str) -> None:
    resp = getattr(client, method)(path)
    assert resp.status_code == 401


# ── CRUD: Basic Info ────────────────────────────────────────────


def test_basic_info_crud(client: TestClient) -> None:
    headers = auth_header(client, "biuser")

    # Create
    resp = client.post("/api/basic-info", json={
        "full_name": "田中太郎",
        "name_furigana": "たなか たろう",
        "record_date": "2026-03-12",
        "qualifications": [],
    }, headers=headers)
    assert resp.status_code == 201
    info_id = resp.json()["id"]

    # Read latest
    resp = client.get("/api/basic-info/latest", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "田中太郎"

    # Update
    resp = client.put(f"/api/basic-info/{info_id}", json={
        "full_name": "田中花子",
        "name_furigana": "たなか はなこ",
        "record_date": "2026-03-12",
        "qualifications": [],
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "田中花子"


# ── CRUD: Resume ────────────────────────────────────────────────


def test_resume_crud(client: TestClient) -> None:
    headers = auth_header(client, "resumeuser")

    resp = client.post("/api/resumes", json={
        "career_summary": "キャリアサマリー",
        "self_pr": "自己PR",
        "experiences": [],
    }, headers=headers)
    assert resp.status_code == 201
    resume_id = resp.json()["id"]

    resp = client.get("/api/resumes/latest", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["career_summary"] == "キャリアサマリー"

    resp = client.put(f"/api/resumes/{resume_id}", json={
        "career_summary": "更新済みサマリー",
        "self_pr": "自己PR",
        "experiences": [],
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["career_summary"] == "更新済みサマリー"


# ── CRUD: Rirekisho ─────────────────────────────────────────────


def test_rirekisho_crud(client: TestClient) -> None:
    headers = auth_header(client, "rirekishouser")

    resp = client.post("/api/rirekisho", json={

        "gender": "male",
        "prefecture": "東京都",
        "address": "渋谷区神南1-1-1",
        "address_furigana": "しぶやく じんなん",
        "email": "test@example.com",
        "phone": "09012345678",
        "motivation": "御社の事業に共感しました",
        "educations": [],
        "work_histories": [],
    }, headers=headers)
    assert resp.status_code == 201
    rirekisho_id = resp.json()["id"]

    resp = client.get("/api/rirekisho/latest", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["prefecture"] == "東京都"

    resp = client.put(f"/api/rirekisho/{rirekisho_id}", json={

        "gender": "female",
        "prefecture": "東京都",
        "address": "渋谷区神南2-2-2",
        "address_furigana": "しぶやく じんなん",
        "email": "test2@example.com",
        "phone": "09087654321",
        "motivation": "更新済み志望動機",
        "educations": [],
        "work_histories": [],
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["gender"] == "female"


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
    resp = client.post("/api/resumes", json={
        "career_summary": "サマリー",
        "self_pr": "自己PR",
        "experiences": [],
    }, headers=headers)
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
    resp = client.post("/api/rirekisho", json={

        "gender": "male",
        "prefecture": "東京都",
        "address": "渋谷区神南1-1-1",
        "address_furigana": "しぶやく じんなん",
        "email": "test@example.com",
        "phone": "09012345678",
        "motivation": "志望動機",
        "educations": [],
        "work_histories": [],
    }, headers=headers)
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
