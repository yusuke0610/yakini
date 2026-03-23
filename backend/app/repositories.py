import logging
from typing import Any, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm.attributes import set_committed_value

from .date_utils import parse_iso_date, parse_year_month
from .encryption import decrypt_field, encrypt_field
from .models import (
    BasicInfo,
    BasicInfoQualification,
    BlogAccount,
    BlogArticle,
    BlogArticleTag,
    MPrefecture,
    MQualification,
    MTechnologyStack,
    Resume,
    ResumeClient,
    ResumeExperience,
    ResumeProject,
    ResumeProjectPhase,
    ResumeProjectTechnologyStack,
    ResumeProjectTeamMember,
    Rirekisho,
    RirekishoEducation,
    RirekishoWorkHistory,
    User,
)

_ENCRYPTED_RIREKISHO_FIELDS = {"email", "phone", "postal_code", "address"}

T = TypeVar("T")


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, username: str, hashed_password: str, email: str | None = None) -> User:
        user = User(username=username, hashed_password=hashed_password, email=email)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(User.username == username))

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_github_id(self, github_id: int) -> User | None:
        return self.db.scalar(select(User).where(User.github_id == github_id))

    def create_github_user(self, username: str, github_id: int) -> User:
        user = User(username=username, hashed_password="", github_id=github_id)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(User)) or 0


class SingleUserDocumentRepository:
    """1ユーザー1件のドキュメント用共通リポジトリ。"""

    _model: type
    _loader_options: tuple[Any, ...] = ()

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def _statement(self):
        statement = select(self._model).where(self._model.user_id == self.user_id)
        for option in self._loader_options:
            statement = statement.options(option)
        return statement

    def get_current(self) -> Any:
        return self.db.scalar(self._statement())

    def get_latest(self) -> Any:
        return self.get_current()

    def get_by_id(self, entity_id: str) -> Any:
        statement = self._statement().where(self._model.id == entity_id)
        return self.db.scalar(statement)

    def create(self, payload: dict[str, Any]) -> Any:
        if self.get_current():
            raise ValueError("document.already_exists")
        entity = self._model(user_id=self.user_id)
        self._apply_payload(entity, payload)
        self.db.add(entity)
        self.db.commit()
        return self.get_by_id(entity.id)

    def update(self, entity: Any, payload: dict[str, Any]) -> Any:
        self._apply_payload(entity, payload)
        self.db.commit()
        return self.get_by_id(entity.id)

    def _apply_payload(self, entity: Any, payload: dict[str, Any]) -> None:
        raise NotImplementedError


class BasicInfoRepository(SingleUserDocumentRepository):
    _model = BasicInfo
    _loader_options = (selectinload(BasicInfo.qualification_rows),)

    def _apply_payload(self, entity: BasicInfo, payload: dict[str, Any]) -> None:
        entity.full_name = payload["full_name"]
        entity.name_furigana = payload["name_furigana"]
        entity.record_date_value = parse_iso_date(payload["record_date"])
        entity.qualification_rows = [
            BasicInfoQualification(
                sort_order=index,
                acquired_date_value=parse_iso_date(item["acquired_date"]),
                name=item["name"],
            )
            for index, item in enumerate(payload.get("qualifications", []))
        ]


class ResumeRepository(SingleUserDocumentRepository):
    _model = Resume
    _loader_options = (
        selectinload(Resume.experience_rows).selectinload(ResumeExperience.client_rows),
        selectinload(Resume.experience_rows)
        .selectinload(ResumeExperience.client_rows)
        .selectinload(ResumeClient.project_rows)
        .selectinload(ResumeProject.team_member_rows),
        selectinload(Resume.experience_rows)
        .selectinload(ResumeExperience.client_rows)
        .selectinload(ResumeClient.project_rows)
        .selectinload(ResumeProject.technology_stack_rows),
        selectinload(Resume.experience_rows)
        .selectinload(ResumeExperience.client_rows)
        .selectinload(ResumeClient.project_rows)
        .selectinload(ResumeProject.phase_rows),
    )

    def _apply_payload(self, entity: Resume, payload: dict[str, Any]) -> None:
        entity.career_summary = payload["career_summary"]
        entity.self_pr = payload["self_pr"]
        entity.experience_rows = [
            self._build_experience_row(index, experience)
            for index, experience in enumerate(payload.get("experiences", []))
        ]

    def _build_experience_row(self, index: int, payload: dict[str, Any]) -> ResumeExperience:
        return ResumeExperience(
            sort_order=index,
            company=payload["company"],
            business_description=payload["business_description"],
            start_date_value=parse_year_month(payload["start_date"]),
            end_date_value=(
                parse_year_month(payload["end_date"]) if payload.get("end_date") else None
            ),
            is_current=payload.get("is_current", False),
            employee_count=payload.get("employee_count", ""),
            capital=payload.get("capital", ""),
            client_rows=[
                self._build_client_row(client_index, client)
                for client_index, client in enumerate(payload.get("clients", []))
            ],
        )

    def _build_client_row(self, index: int, payload: dict[str, Any]) -> ResumeClient:
        return ResumeClient(
            sort_order=index,
            name=payload.get("name", ""),
            has_client=payload.get("has_client", True),
            project_rows=[
                self._build_project_row(project_index, project)
                for project_index, project in enumerate(payload.get("projects", []))
            ],
        )

    def _build_project_row(self, index: int, payload: dict[str, Any]) -> ResumeProject:
        team = payload.get("team", {})
        return ResumeProject(
            sort_order=index,
            name=payload.get("name", ""),
            start_date_value=parse_year_month(payload["start_date"]),
            end_date_value=(
                parse_year_month(payload["end_date"]) if payload.get("end_date") else None
            ),
            is_current=payload.get("is_current", False),
            role=payload.get("role", ""),
            description=payload.get("description", ""),
            challenge=payload.get("challenge", ""),
            action=payload.get("action", ""),
            result=payload.get("result", ""),
            team_total=team.get("total", ""),
            team_member_rows=[
                ResumeProjectTeamMember(
                    sort_order=member_index,
                    role=member["role"],
                    count=member["count"],
                )
                for member_index, member in enumerate(team.get("members", []))
            ],
            technology_stack_rows=[
                ResumeProjectTechnologyStack(
                    sort_order=stack_index,
                    category=stack["category"],
                    name=stack["name"],
                )
                for stack_index, stack in enumerate(payload.get("technology_stacks", []))
            ],
            phase_rows=[
                ResumeProjectPhase(sort_order=phase_index, name=phase)
                for phase_index, phase in enumerate(payload.get("phases", []))
            ],
        )


class RirekishoRepository(SingleUserDocumentRepository):
    """履歴書リポジトリ。個人情報フィールドの暗号化・復号を行う。"""

    _model = Rirekisho
    _loader_options = (
        selectinload(Rirekisho.education_rows),
        selectinload(Rirekisho.work_history_rows),
    )

    def _encrypt_value(self, field: str, value: str) -> str:
        if field in _ENCRYPTED_RIREKISHO_FIELDS:
            return encrypt_field(value)
        return value

    def _decrypt_rirekisho(self, rirekisho: Rirekisho) -> None:
        for field in _ENCRYPTED_RIREKISHO_FIELDS:
            value = getattr(rirekisho, field, None)
            if isinstance(value, str):
                try:
                    set_committed_value(rirekisho, field, decrypt_field(value))
                except Exception:
                    logging.warning(
                        "Failed to decrypt field %s, returning raw value",
                        field,
                        exc_info=True,
                    )

    def _apply_payload(self, entity: Rirekisho, payload: dict[str, Any]) -> None:
        entity.gender = payload["gender"]
        entity.birthday_value = parse_iso_date(payload["birthday"])
        entity.prefecture = payload["prefecture"]
        entity.postal_code = self._encrypt_value("postal_code", payload["postal_code"])
        entity.address = self._encrypt_value("address", payload["address"])
        entity.address_furigana = payload["address_furigana"]
        entity.email = self._encrypt_value("email", payload["email"])
        entity.phone = self._encrypt_value("phone", payload["phone"])
        entity.motivation = payload.get("motivation", "")
        entity.personal_preferences = payload.get("personal_preferences", "")
        entity.photo = payload.get("photo")
        entity.education_rows = [
            RirekishoEducation(
                sort_order=index,
                occurred_on_value=parse_year_month(item["date"]),
                name=item["name"],
            )
            for index, item in enumerate(payload.get("educations", []))
        ]
        entity.work_history_rows = [
            RirekishoWorkHistory(
                sort_order=index,
                occurred_on_value=parse_year_month(item["date"]),
                name=item["name"],
            )
            for index, item in enumerate(payload.get("work_histories", []))
        ]

    def create(self, payload: dict[str, Any]) -> Rirekisho:
        rirekisho = super().create(payload)
        self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def get_current(self) -> Rirekisho | None:
        rirekisho = super().get_current()
        if rirekisho:
            self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def get_by_id(self, entity_id: str) -> Rirekisho | None:
        rirekisho = super().get_by_id(entity_id)
        if rirekisho:
            self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def update(self, entity: Any, payload: dict[str, Any]) -> Rirekisho:
        rirekisho = super().update(entity, payload)
        self._decrypt_rirekisho(rirekisho)
        return rirekisho


class BlogAccountRepository:
    """ブログ連携アカウントリポジトリ。"""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def list_by_user(self) -> list[BlogAccount]:
        """ユーザーの連携アカウント一覧を取得する。"""
        statement = (
            select(BlogAccount)
            .where(BlogAccount.user_id == self.user_id)
            .order_by(BlogAccount.created_at)
        )
        return list(self.db.scalars(statement).all())

    def get_by_id(self, account_id: str) -> BlogAccount | None:
        """アカウントIDで取得する。"""
        statement = (
            select(BlogAccount)
            .where(BlogAccount.id == account_id)
            .where(BlogAccount.user_id == self.user_id)
        )
        return self.db.scalar(statement)

    def get_by_platform(self, platform: str) -> BlogAccount | None:
        """プラットフォーム名で取得する。"""
        statement = (
            select(BlogAccount)
            .where(BlogAccount.user_id == self.user_id)
            .where(BlogAccount.platform == platform)
        )
        return self.db.scalar(statement)

    def upsert(self, platform: str, username: str) -> BlogAccount:
        """アカウントを登録または更新する。"""
        existing = self.get_by_platform(platform)
        if existing:
            existing.username = username
            self.db.commit()
            self.db.refresh(existing)
            return existing
        account = BlogAccount(user_id=self.user_id, platform=platform, username=username)
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def delete(self, account_id: str) -> bool:
        """アカウントを削除する。"""
        account = self.get_by_id(account_id)
        if not account:
            return False
        self.db.delete(account)
        self.db.commit()
        return True


class BlogArticleRepository:
    """ブログ記事リポジトリ。"""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def list_by_user(self, platform: str | None = None) -> list[BlogArticle]:
        """ユーザーの記事一覧を取得する。platformフィルタ任意。"""
        statement = (
            select(BlogArticle)
            .join(BlogArticle.account)
            .where(BlogAccount.user_id == self.user_id)
            .options(
                selectinload(BlogArticle.account),
                selectinload(BlogArticle.tag_rows),
            )
        )
        if platform:
            statement = statement.where(BlogAccount.platform == platform)
        statement = statement.order_by(
            BlogArticle.published_at_value.desc(),
            BlogArticle.created_at.desc(),
        )
        return list(self.db.scalars(statement).all())

    def upsert_many(self, articles: list[dict]) -> int:
        """記事を一括登録・更新する。戻り値は新規追加件数。"""
        normalized_articles = [self._normalize_article(article) for article in articles]
        if not normalized_articles:
            return 0

        account_ids = {article["account_id"] for article in normalized_articles}
        external_ids = {article["external_id"] for article in normalized_articles}
        existing_statement = (
            select(BlogArticle)
            .join(BlogArticle.account)
            .where(BlogAccount.user_id == self.user_id)
            .where(BlogArticle.account_id.in_(account_ids))
            .where(BlogArticle.external_id.in_(external_ids))
            .options(selectinload(BlogArticle.tag_rows))
        )
        existing_articles = list(self.db.scalars(existing_statement).all())
        existing_map = {
            (article.account_id, article.external_id): article for article in existing_articles
        }

        added = 0
        for article in normalized_articles:
            key = (article["account_id"], article["external_id"])
            existing = existing_map.get(key)
            if existing:
                self._apply_article_payload(existing, article)
                continue

            entity = BlogArticle(account_id=article["account_id"])
            self._apply_article_payload(entity, article)
            self.db.add(entity)
            existing_map[key] = entity
            added += 1

        self.db.commit()
        return added

    def count_by_user(self) -> int:
        """ユーザーの記事数を取得する。"""
        return (
            self.db.scalar(
                select(func.count())
                .select_from(BlogArticle)
                .join(BlogArticle.account)
                .where(BlogAccount.user_id == self.user_id)
            )
            or 0
        )

    def delete_by_account(self, account_id: str) -> int:
        """アカウントに紐づく記事を全削除する。戻り値は削除件数。"""
        articles = list(
            self.db.scalars(
                select(BlogArticle)
                .join(BlogArticle.account)
                .where(BlogAccount.user_id == self.user_id)
                .where(BlogArticle.account_id == account_id)
            ).all()
        )
        count = len(articles)
        for article in articles:
            self.db.delete(article)
        self.db.commit()
        return count

    def _normalize_article(self, article: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(article)
        normalized["external_id"] = normalized.get("external_id") or normalized["url"]
        return normalized

    def _apply_article_payload(self, entity: BlogArticle, payload: dict[str, Any]) -> None:
        entity.external_id = payload["external_id"]
        entity.title = payload["title"]
        entity.url = payload["url"]
        entity.published_at_value = (
            parse_iso_date(payload["published_at"]) if payload.get("published_at") else None
        )
        entity.likes_count = payload.get("likes_count", 0)
        entity.summary = payload.get("summary")
        entity.tag_rows = [
            BlogArticleTag(sort_order=index, name=tag)
            for index, tag in enumerate(payload.get("tags", []))
        ]


class BaseMasterRepository:
    """マスタデータ（資格・都道府県）の共通リポジトリ。"""

    _model: type

    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list:
        """マスタ一覧を取得する。"""
        statement = select(self._model).order_by(self._model.sort_order, self._model.name)
        return list(self.db.scalars(statement).all())

    def create(self, name: str, sort_order: int = 0) -> Any:
        """マスタを作成する。"""
        item = self._model(name=name, sort_order=sort_order)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item_id: str, name: str, sort_order: int = 0) -> Any:
        """マスタを更新する。"""
        item = self.db.scalar(select(self._model).where(self._model.id == item_id))
        if not item:
            return None
        item.name = name
        item.sort_order = sort_order
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: str) -> bool:
        """マスタを削除する。"""
        item = self.db.scalar(select(self._model).where(self._model.id == item_id))
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    def seed_if_empty(self, items: list[dict]) -> None:
        """テーブルが空の場合のみ一括投入する。"""
        count = self.db.scalar(select(func.count()).select_from(self._model))
        if count:
            return
        for item in items:
            self.db.add(self._model(**item))
        self.db.commit()


class MQualificationRepository(BaseMasterRepository):
    """資格マスタリポジトリ。"""

    _model = MQualification


class MPrefectureRepository(BaseMasterRepository):
    """都道府県マスタリポジトリ。"""

    _model = MPrefecture


class MTechnologyStackRepository(BaseMasterRepository):
    """技術スタックマスタリポジトリ。category フィールドを追加で管理する。"""

    _model = MTechnologyStack

    def list_by_category(self, category: str) -> list[MTechnologyStack]:
        """カテゴリ別に技術スタックマスタを取得する。"""
        statement = (
            select(MTechnologyStack)
            .where(MTechnologyStack.category == category)
            .order_by(MTechnologyStack.sort_order, MTechnologyStack.name)
        )
        return list(self.db.scalars(statement).all())

    def create(self, category: str, name: str, sort_order: int = 0) -> MTechnologyStack:
        """技術スタックマスタを作成する。"""
        item = MTechnologyStack(category=category, name=name, sort_order=sort_order)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(
        self, item_id: str, category: str, name: str, sort_order: int = 0
    ) -> MTechnologyStack | None:
        """技術スタックマスタを更新する。"""
        item = self.db.scalar(select(MTechnologyStack).where(MTechnologyStack.id == item_id))
        if not item:
            return None
        item.category = category
        item.name = name
        item.sort_order = sort_order
        self.db.commit()
        self.db.refresh(item)
        return item
