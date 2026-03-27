from sqlalchemy import func, select

from ..models import User


class UserRepository:
    def __init__(self, db):
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
