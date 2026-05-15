"""スキルタクソノミパッケージ。

既存のインポートパスとの互換性を保つため、すべての公開シンボルを re-export する。
"""

from .classifier import (
    SKILL_CATEGORIES,
    get_all_skills,
    get_skill_category,
)
from .keyword_map import DESCRIPTION_KEYWORDS
from .language_map import LANGUAGE_TO_SKILL
from .ownership_map import (
    FILE_SKILL_MAP,
    FRAMEWORK_SKILL_MAP,
    FRAMEWORK_TO_TOPICS,
    LANG_SKILL_MAP,
    LANG_SKILL_THRESHOLD,
    TOPIC_SKILL_MAP,
)
from .topic_map import TOPIC_TO_SKILLS

__all__ = [
    "DESCRIPTION_KEYWORDS",
    "FILE_SKILL_MAP",
    "FRAMEWORK_SKILL_MAP",
    "FRAMEWORK_TO_TOPICS",
    "LANGUAGE_TO_SKILL",
    "LANG_SKILL_MAP",
    "LANG_SKILL_THRESHOLD",
    "SKILL_CATEGORIES",
    "TOPIC_SKILL_MAP",
    "TOPIC_TO_SKILLS",
    "get_all_skills",
    "get_skill_category",
]
