# LLM 入力データポリシー

LLM へ送信するデータは以下の3分類で管理する。

---

## フィールド分類一覧

### A分類 — そのまま送ってよい

技術的な事実・統計であり、個人を特定できる情報を含まない。

| フィールド | 説明 |
|---|---|
| `qualifications[].name` | 資格名 |
| `qualifications[].acquired_date` | 資格取得日 |
| `technology_stacks[].name` | 技術スタック名 |
| `project.{start_date, end_date}` | 案件期間 |
| `project.phases` | 担当フェーズ |
| `analysis.repos_analyzed` | 分析リポジトリ数 |
| `analysis.unique_skills` | ユニークスキル数 |
| `analysis.languages` | 使用言語と割合 |
| `analysis.position_scores` | ポジションスコア（backend/frontend等） |
| `analysis.missing_skills` | 不足スキル一覧 |
| `analysis.repositories[].skills` | リポジトリ検出スキル |
| `blog.tags` | 記事タグ |
| `blog.likes_count` | いいね数 |

### B分類 — マスキングして送る

固有名詞・自由記述であり、`SanitizeContext` を通じてラベルに置換してから送信する。

| フィールド | 変換内容 | 関数 |
|---|---|---|
| `experience.company` | `[企業A]` `[企業B]`... | `context.register_company()` |
| `client.name` | `[顧客A]` `[顧客B]`... | `context.register_customer()` |
| `project.name` | `[案件A]` `[案件B]`... | `sanitize_project_name()` |
| `project.description` | 辞書登録済み名称をラベルに置換 | `sanitize_text()` |
| `resume.career_summary` | 辞書登録済み名称をラベルに置換 | `sanitize_text()` |
| `blog_cache.summary` | 辞書登録済み名称をラベルに置換 | `sanitize_text()` |
| `blog.article.title` | 辞書登録済み名称をラベルに置換 | `sanitize_text()` |
| `blog.article.summary` | 辞書登録済み名称をラベルに置換 | `sanitize_text()` |
| `work_histories[].name` | `[案件A]` `[案件B]`... | `sanitize_work_history_name()` |

> **注意**: 辞書未登録の固有名詞は現状マスキングされない（MVP仕様）。
> NER による自動抽出はスコープ外。

### C分類 — 原則送らない

氏名・個人情報であり、`strip_prohibited_fields()` で除去してから渡す。

| フィールド | 理由 |
|---|---|
| `full_name` | 氏名（個人識別情報） |
| `email` | メールアドレス |
| `motivation` | 志望動機 |
| `personal_preferences` | 個人の嗜好 |
| `username` | ユーザーID（サービス内識別子） |

> 住所・郵便番号・生年月日・電話番号・名前ふりがな・写真はシステム上入力されないため対象外。

---

## SanitizeContext の使い方

`SanitizeContext` は1リクエストスコープで生成し、複数のフィールドにわたって共有する。
これにより「株式会社テスト」が複数箇所に出ても常に `[企業A]` に統一される。

```python
from app.services.llm.sanitizer import SanitizeContext, sanitize_text, sanitize_project_name

# リクエスト開始時に生成
context = SanitizeContext()

# 構造化フィールドから事前登録
context.register_company("株式会社テスト")      # → [企業A]
context.register_customer("顧客企業株式会社")    # → [顧客A]
context.register_project("基幹システム刷新")     # → [案件A]

# 自由記述のマスキング
masked = sanitize_text("株式会社テストで基幹システム刷新を担当", context)
# → "[企業A]で[案件A]を担当"

# 案件名のラベル化
label = sanitize_project_name("基幹システム刷新", context)
# → "[案件A]"（既登録のため同じラベル）
```

---

## 新しい LLM 入力フィールドを追加する際の判断フロー

```
新しいフィールドをプロンプトに追加しようとしている
         ↓
そのフィールドは個人を特定できるか？
  YES → C分類: strip_prohibited_fields() に追加し、送信しない
  NO  ↓
そのフィールドは固有名詞・案件名・社名を含む可能性があるか？
  YES → B分類: sanitize_text() または register_*() でマスキング
  NO  ↓
A分類: そのまま渡してよい
```

---

## ラベルの番号体系

- 企業: `[企業A]` `[企業B]` ... `[企業Z]` `[企業27]` ...
- 顧客: `[顧客A]` `[顧客B]` ...
- 案件: `[案件A]` `[案件B]` ...
- プロダクト: `[プロダクトA]` ...
- 業務ドメイン: `[業務ドメインA]` ...

ラベルは `SanitizeContext` がリクエスト単位で採番するため、
リクエストをまたいでラベルが変わることは許容する（MVP仕様）。
