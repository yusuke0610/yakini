"""Repository 層。"""

from .base import BaseMasterRepository, SingleUserDocumentRepository
from .basic_info import BasicInfoRepository
from .blog import BlogAccountRepository, BlogArticleRepository
from .master_data import MPrefectureRepository, MQualificationRepository, MTechnologyStackRepository
from .resume import ResumeRepository
from .rirekisho import RirekishoRepository
from .user import UserRepository

__all__ = [
    "BaseMasterRepository",
    "BasicInfoRepository",
    "BlogAccountRepository",
    "BlogArticleRepository",
    "MPrefectureRepository",
    "MQualificationRepository",
    "MTechnologyStackRepository",
    "ResumeRepository",
    "RirekishoRepository",
    "SingleUserDocumentRepository",
    "UserRepository",
]
