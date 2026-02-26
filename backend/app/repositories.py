from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .encryption import decrypt_field, encrypt_field
from .models import BasicInfo, Resume, Resume, User

_ENCRYPTED_Resume_FIELDS = {"email", "phone", "postal_code", "address"}


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, username: str, hashed_password: str) -> User:
        user = User(username=username, hashed_password=hashed_password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return self.db.scalar(statement)

    def count(self) -> int:
        statement = select(func.count()).select_from(User)
        return self.db.scalar(statement) or 0


class BasicInfoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict[str, Any]) -> BasicInfo:
        basic_info = BasicInfo(**payload)
        self.db.add(basic_info)
        self.db.commit()
        self.db.refresh(basic_info)
        return basic_info

    def get_latest(self) -> BasicInfo | None:
        statement = (
            select(BasicInfo).order_by(BasicInfo.updated_at.desc()).limit(1)
        )
        return self.db.scalar(statement)

    def get_by_id(self, basic_info_id: str) -> BasicInfo | None:
        return self.db.get(BasicInfo, basic_info_id)

    def update(
        self, basic_info: BasicInfo, payload: dict[str, Any]
    ) -> BasicInfo:
        for field, value in payload.items():
            setattr(basic_info, field, value)

        self.db.commit()
        self.db.refresh(basic_info)
        return basic_info


class ResumeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict[str, Any]) -> Resume:
        resume = Resume(**payload)
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get_by_id(self, resume_id: str) -> Resume | None:
        return self.db.get(Resume, resume_id)

    def update(self, resume: Resume, payload: dict[str, Any]) -> Resume:
        for field, value in payload.items():
            setattr(resume, field, value)

        self.db.commit()
        self.db.refresh(resume)
        return resume


class ResumeRepository:
    def __init__(self, db: Session):
        self.db = db

    def _encrypt_payload(
        self, payload: dict[str, Any]
    ) -> dict[str, Any]:
        result = dict(payload)
        for field in _ENCRYPTED_Resume_FIELDS:
            if field in result and isinstance(result[field], str):
                result[field] = encrypt_field(result[field])
        return result

    def _decrypt_Resume(self, Resume: Resume) -> None:
        for field in _ENCRYPTED_Resume_FIELDS:
            value = getattr(Resume, field, None)
            if isinstance(value, str):
                try:
                    setattr(Resume, field, decrypt_field(value))
                except Exception:
                    pass  # 暗号化前のデータはそのまま返す

    def create(self, payload: dict[str, Any]) -> Resume:
        Resume = Resume(**self._encrypt_payload(payload))
        self.db.add(Resume)
        self.db.commit()
        self.db.refresh(Resume)
        self._decrypt_Resume(Resume)
        return Resume

    def get_by_id(self, Resume_id: str) -> Resume | None:
        Resume = self.db.get(Resume, Resume_id)
        if Resume:
            self._decrypt_Resume(Resume)
        return Resume

    def update(
        self, Resume: Resume, payload: dict[str, Any]
    ) -> Resume:
        for field, value in self._encrypt_payload(payload).items():
            setattr(Resume, field, value)

        self.db.commit()
        self.db.refresh(Resume)
        self._decrypt_Resume(Resume)
        return Resume
