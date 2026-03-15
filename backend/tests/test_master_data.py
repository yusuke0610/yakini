import os

from app.repositories import MPrefectureRepository, MQualificationRepository, MTechnologyStackRepository
from app.seed import seed_master_data


def test_list_qualifications(client, db_session):
    """GETで資格マスタが取得できること。"""
    MQualificationRepository(db_session).create("テスト資格", 1)
    response = client.get("/api/master-data/qualification")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "テスト資格"


def test_list_technology_stacks(client, db_session):
    """GETで技術スタックマスタが取得できること。"""
    MTechnologyStackRepository(db_session).create("language", "Python", 1)
    response = client.get("/api/master-data/technology-stack")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Python"
    assert data[0]["category"] == "language"


def test_list_prefectures(client, db_session):
    """GETで都道府県マスタが取得できること。"""
    MPrefectureRepository(db_session).create("東京都", 13)
    response = client.get("/api/master-data/prefecture")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "東京都"


def test_create_qualification_requires_admin(client):
    """admin tokenなしでPOSTすると認証エラーが返ること。"""
    os.environ["ADMIN_TOKEN"] = "test-admin-token"
    response = client.post(
        "/api/master-data/qualification",
        json={"name": "テスト", "sort_order": 0},
    )
    assert response.status_code in (401, 403)


def test_create_qualification(client):
    """admin tokenありでPOSTすると201が返ること。"""
    os.environ["ADMIN_TOKEN"] = "test-admin-token"
    response = client.post(
        "/api/master-data/qualification",
        json={"name": "テスト資格", "sort_order": 1},
        headers={"Authorization": "Bearer test-admin-token"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "テスト資格"


def test_seed_idempotent(db_session):
    """2回実行してもデータが重複しないこと。"""
    seed_master_data(db_session)
    count_first = len(MPrefectureRepository(db_session).list_all())
    seed_master_data(db_session)
    count_second = len(MPrefectureRepository(db_session).list_all())
    assert count_first == count_second == 47
