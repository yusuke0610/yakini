---
name: backend_refacter
description: Use when reviewing or planning refactors for the DevForge FastAPI backend, especially for maintainability, redundant or missing unit tests, oversized modules or classes, responsibility separation, and directory structure changes. Trigger on requests such as “backend のリファクタリングを見て”, “保守性を確認”, “不要な単体テスト”, “単体テストは十分か”, “責務分離”, or “構成見直し”.
---

# Backend Refactor Review

## 先に読む

- `.claude/CLAUDE.md`
- `.claude/rules/backend/architecture.md`
- `.claude/rules/backend/python.md`
- `.claude/rules/backend/database.md`
- `.claude/rules/backend/auth-security.md`
- LLM やブログ AI 分析を含む場合だけ `.claude/rules/backend/llm.md`

## 対象

- `backend/app/**`
- `backend/tests/**`
- `backend/alembic_migrations/**`
- 必要に応じて `backend/scripts/**`, `backend/Dockerfile`, `backend/requirements.txt`

## 目的

この skill の目的は、単なる感想ではなく「どこが保守しづらいか」「どのテストが低価値か」「どのテストが足りないか」「どの責務を分離すべきか」を、根拠付きでレビューすることです。

必ず以下を区別してください。

- 低価値テスト: 価値は低いが残しても害が少ない
- 不要テスト: 他のテストで十分に守られており、保守コストが勝つ
- テスト不足: バグが入りやすいのにカバーされていない
- 設計問題: モジュール分割や責務境界が悪く、変更容易性を落としている

## 調査の進め方

### 1. インベントリ

- `rg --files backend/app backend/tests backend/alembic_migrations`
- 大きいファイルを洗う: `rg --files backend/app backend/tests | xargs wc -l | sort -nr | head -n 30`
- まず以下の境界で構造を把握する
  - router: HTTP 入出力、認証、rate limit、エラー変換
  - service: ビジネスロジック、外部 API、LLM、PDF/Markdown 生成
  - repository: 永続化と問い合わせ
  - schema/model: API 契約、DB 契約
  - tests: ルータ、サービス、純粋関数、外部依存のモック

### 2. 保守性レビュー

以下のどれかに当てはまれば、責務分離候補として扱います。

- router が入力検証に加えて、ドメイン判断、永続化、外部 API 制御まで持っている
- service が I/O、ビジネスルール、整形、キャッシュ更新を同時に持つ
- repository が複数 aggregate の知識を横断しすぎている
- schema/model の変更理由が複数あり、1つの変更で広範囲に波及する
- 例外変換やメッセージ解決が各所に分散し、統一ルールが崩れている

サイズの目安は補助指標です。行数だけで断定しないこと。

- module が 400 行超で責務が複数ある
- class が 200 行超で状態と振る舞いが混在している
- router 関数が 40 行超で分岐や外部依存が多い
- service 関数が 60 行超で「問い合わせ」「判定」「整形」「保存」を連続で行う

### 3. 単体テストレビュー

不要と判定する条件:

- 同一分岐を別名で重複テストしている
- framework やライブラリの既知動作しか見ていない
- 実装詳細のモックや call count に強く依存し、仕様変更なしで壊れやすい
- 単純な schema/dto の受け渡しだけで、ドメイン価値を守っていない
- より上位のテストが同じ失敗を十分に検知できる

不要と断定してはいけない条件:

- 単純でも境界条件や回帰バグを実際に防いでいる
- セキュリティ、認可、例外変換、外部 API 失敗時の挙動を守っている
- SQLite 制約、ユニーク制約、子テーブル cascade など壊れやすい契約を守っている

不足と判定する観点:

- 純粋関数の分岐、スコア計算、日付処理、マッピング
- router の認証、認可、validation、HTTP status、エラーメッセージ変換
- repository の upsert、一意制約、削除 cascade、ユーザー境界
- 外部 API や LLM の timeout / unavailable / partial failure
- マイグレーション後の不変条件
- セキュリティ設定: cookie, CSRF, GitHub OAuth state, rate limit

### 4. ディレクトリ構成レビュー

以下を見ます。

- `routers/`, `services/`, `repositories.py`, `models.py`, `schemas.py` の分割単位が適切か
- 1ファイルに複数ドメインの知識が混ざっていないか
- `services/` 配下が機能別サブパッケージで分けられるか
- `repositories.py` の肥大化を package 化で抑えるべきか
- PDF / Markdown / Intelligence / Blog のような機能境界がディレクトリ境界に反映されているか

構成変更を提案するときは、必ず次をセットで出します。

- 何が今の問題か
- どのファイルをどこへ分けるか
- 分けた後に依存方向がどう単純化されるか
- 今は見送るべき変更は何か

## レビューの厳しさ

- 「巨大だから分割」ではなく、「変更理由が複数だから分割」で判断する
- 「テスト数が少ない」ではなく、「高リスク経路が無防備」で判断する
- 「ディレクトリが気に入らない」ではなく、「探索コストや依存関係が悪い」で判断する

## 推奨出力フォーマット

````markdown
# Backend Refactor Review

## Verdict
- 保守性の総評を 3-5 行で要約

## Findings
### High
- [path/to/file.py:line] 問題点。なぜ危険か。どう分割または整理するか。

### Medium
- ...

### Low
- ...

## Test Review
### Remove or Merge
- [path] なぜ低価値か。削除しても何がカバーされるか。

### Add
- [path or module] どのケースを追加すべきか。守る仕様は何か。

## Structure Review
### Oversized Modules or Classes
- [path] 責務が何個あるか。どう切るか。

### Directory Changes
- 提案する target 構成

```text
backend/app/
  routers/
  services/
  repositories/
  ...
```

## Refactor Plan
1. まず何を分けるか
2. 次にどのテストを整理するか
3. 最後に何を検証するか

## Validation
- 実行したコマンド
- 未実行ならその理由
````

## 最低限の検証コマンド

- `cd backend && PYTHONPATH=. .venv/bin/python -m ruff check app tests alembic_migrations`
- `cd backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests`

コード変更を含む場合は、少なくとも影響範囲のテストを回し、必要なら全件を回してください。
