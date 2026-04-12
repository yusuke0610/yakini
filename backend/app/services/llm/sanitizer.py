"""LLM 送信前のデータサニタイズモジュール。

エンティティを3分類して処理する:
- A分類: そのまま送ってよい（スキル名・言語名・ポジションスコア等）
- B分類: マスキングして送る（企業名・顧客名・案件名・自由記述テキスト）
- C分類: 送らない（氏名・メール・志望動機等）

マスキングは辞書ベースで同一セッション（SanitizeContext）内の一貫性を保つ。
NER 等の自動抽出はスコープ外。辞書への登録は構造化フィールドから事前に行う。

住所・郵便番号・生年月日・電話番号・名前ふりがな・写真はシステム上入力されないため除外。
"""

from dataclasses import dataclass, field

# C分類（原則送らない）フィールド一覧
# ※ 住所・郵便番号・生年月日・電話番号・名前ふりがな・写真はシステム上入力されないため除外
_PROHIBITED_FIELDS: frozenset[str] = frozenset(
    {
        "full_name",
        "email",
        "motivation",
        "personal_preferences",
        "username",
    }
)


def _alpha_label(prefix: str, index: int) -> str:
    """0起算インデックスから「[企業A]」「[企業B]」... のラベルを生成する。

    26以上のインデックスは数値サフィックス（[企業27]等）にフォールバックする。
    """
    suffix = chr(ord("A") + index) if index < 26 else str(index + 1)
    return f"[{prefix}{suffix}]"


@dataclass
class SanitizeContext:
    """セッション単位でエンティティラベルの一貫性を保つ状態管理。

    同一の raw 名が複数箇所に出現しても同じラベルに変換される。
    1リクエストスコープで生成し、DB保存・キャッシュは不要。
    """

    companies: dict[str, str] = field(default_factory=dict)
    """raw 企業名 → 「[企業A]」「[企業B]」..."""
    customers: dict[str, str] = field(default_factory=dict)
    """raw 顧客名 → 「[顧客A]」「[顧客B]」..."""
    projects: dict[str, str] = field(default_factory=dict)
    """raw 案件名 → 「[案件A]」「[案件B]」..."""
    products: dict[str, str] = field(default_factory=dict)
    """raw プロダクト名 → 「[プロダクトA]」..."""
    domains: dict[str, str] = field(default_factory=dict)
    """raw 業務ドメイン名 → 「[業務ドメインA]」..."""

    def register_company(self, name: str) -> str:
        """企業名をコンテキストに登録してラベルを返す。空文字は登録しない。"""
        if not name:
            return name
        if name not in self.companies:
            self.companies[name] = _alpha_label("企業", len(self.companies))
        return self.companies[name]

    def register_customer(self, name: str) -> str:
        """顧客名をコンテキストに登録してラベルを返す。空文字は登録しない。"""
        if not name:
            return name
        if name not in self.customers:
            self.customers[name] = _alpha_label("顧客", len(self.customers))
        return self.customers[name]

    def register_project(self, name: str) -> str:
        """案件名をコンテキストに登録してラベルを返す。空文字は登録しない。"""
        if not name:
            return name
        if name not in self.projects:
            self.projects[name] = _alpha_label("案件", len(self.projects))
        return self.projects[name]

    def register_product(self, name: str) -> str:
        """プロダクト名をコンテキストに登録してラベルを返す。空文字は登録しない。"""
        if not name:
            return name
        if name not in self.products:
            self.products[name] = _alpha_label("プロダクト", len(self.products))
        return self.products[name]

    def register_domain(self, name: str) -> str:
        """業務ドメイン名をコンテキストに登録してラベルを返す。空文字は登録しない。"""
        if not name:
            return name
        if name not in self.domains:
            self.domains[name] = _alpha_label("業務ドメイン", len(self.domains))
        return self.domains[name]

    def _all_masks(self) -> dict[str, str]:
        """全カテゴリの辞書を統合して返す。

        後から更新されたカテゴリが優先されるよう、具体性の高い順に結合する。
        """
        merged: dict[str, str] = {}
        merged.update(self.domains)
        merged.update(self.products)
        merged.update(self.projects)
        merged.update(self.customers)
        merged.update(self.companies)
        return merged


def sanitize_text(text: str, context: SanitizeContext) -> str:
    """自由記述テキストをマスキングして返す。

    辞書に登録済みのエンティティを同一ラベルに置換する。
    長い名前から優先して置換することで部分一致の誤変換を防ぐ。
    辞書未登録の固有名詞はそのまま残る（MVP仕様として許容）。
    """
    if not text:
        return text or ""
    masks = context._all_masks()
    if not masks:
        return text
    masked = text
    for name in sorted(masks.keys(), key=len, reverse=True):
        masked = masked.replace(name, masks[name])
    return masked


def sanitize_project_name(name: str, context: SanitizeContext) -> str:
    """project.name を匿名化ラベルに変換する。"""
    return context.register_project(name)


def strip_prohibited_fields(data: dict) -> dict:
    """C分類（原則送らない）フィールドを dict から除去して返す。

    対象: full_name, email, motivation, personal_preferences, username
    """
    return {k: v for k, v in data.items() if k not in _PROHIBITED_FIELDS}
