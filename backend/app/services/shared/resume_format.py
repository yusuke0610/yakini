"""
職務経歴書フォーマット用の共通ユーティリティ。

PDF（HTML 経由）と Markdown の両ジェネレータで重複していた
- 技術スタックカテゴリの日本語ラベル
- dict / ORM 両対応の属性アクセス

を集約する。

注意:
- 期間表示の `format_period` は PDF（「YYYY 年 MM 月〜現在」）と Markdown（「YYYY-MM - 現在」）で
  意図的に出力フォーマットが異なる。共通化すると出力崩れが起きるためここには置かない。
- HTML エスケープと Markdown エスケープも別物のためここでは扱わない。
"""

from typing import Any

#: 技術スタックカテゴリの日本語ラベル。PDF / Markdown で共通利用する。
CATEGORY_LABELS: dict[str, str] = {
    "language": "言語",
    "framework": "FW",
    "os": "OS",
    "db": "DB",
    "cloud_provider": "クラウド",
    "container": "コンテナ",
    "iac": "IaC",
    "vcs": "バージョン管理",
    "ci_cd": "CI/CD",
    "project_tool": "プロジェクトツール",
    "monitoring": "監視・可観測性",
    "middleware": "ミドルウェア",
    "ai_agent": "AIエージェント",
}


def attr(obj: Any, key: str, default: Any = "") -> Any:
    """dict / ORM オブジェクト両対応の属性アクセスヘルパ。"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)
