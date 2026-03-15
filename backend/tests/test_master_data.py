import os

from app.repositories import MasterDataRepository
from app.seed import seed_master_data


def test_list_master_data_by_category(client, db_session):
    """GETでシード済みデータが取得できること。"""
    repo = MasterDataRepository(db_session)
    repo.create("qualification", "テスト資格", 1)
    response = client.get("/api/master-data/qualification")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "テスト資格"


def test_list_empty_category(client):
    """存在しないカテゴリで空配列が返ること。"""
    response = client.get("/api/master-data/nonexistent")
    assert response.status_code == 200
    assert response.json() == []


def test_create_requires_admin(client):
    """admin tokenなしでPOSTすると認証エラーが返ること。"""
    os.environ["ADMIN_TOKEN"] = "test-admin-token"
    response = client.post(
        "/api/master-data",
        json={"category": "qualification", "name": "テスト", "sort_order": 0},
    )
    assert response.status_code in (401, 403)


def test_create_master_data(client):
    """admin tokenありでPOSTすると201が返ること。"""
    os.environ["ADMIN_TOKEN"] = "test-admin-token"
    response = client.post(
        "/api/master-data",
        json={"category": "qualification", "name": "テスト資格", "sort_order": 1},
        headers={"Authorization": "Bearer test-admin-token"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "テスト資格"
    assert data["category"] == "qualification"


def test_seed_idempotent(db_session):
    """2回実行してもデータが重複しないこと。"""
    seed_master_data(db_session)
    repo = MasterDataRepository(db_session)
    count_first = len(repo.list_by_category("prefecture"))
    seed_master_data(db_session)
    count_second = len(repo.list_by_category("prefecture"))
    assert count_first == count_second == 47
