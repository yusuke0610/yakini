"""キャリアパスパッケージ。

既存のインポートパスとの互換性を保つため、すべての公開シンボルを re-export する。
"""

from .definitions import (
    CAREER_ROLES,
    RoleDefinition,
    get_all_role_names,
    get_entry_roles,
    get_role,
)
from .matcher import RoleMatch, match_skills_to_roles

__all__ = [
    "RoleDefinition",
    "CAREER_ROLES",
    "get_role",
    "get_all_role_names",
    "get_entry_roles",
    "RoleMatch",
    "match_skills_to_roles",
]
