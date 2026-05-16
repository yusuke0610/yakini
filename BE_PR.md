# Backend Refactor: タスクハンドラ失敗パスを NonRetryableError に統一

## Summary

- タスクハンドラの「黙って `return`」と汎用 `RuntimeError` を `NonRetryableError` raise に統一し、worker の `dead_letter` 遷移を確実にする。
- 3 ハンドラの失敗パスを守る回帰テストを新設し、旧契約を固定化していた既存テストを新契約に追従させた。
- CLAUDE.md「タスクハンドラの『黙って return』は禁止」原則の徹底。

## Background

backend のリファクタリングレビューで、以下の不整合が見つかった:

1. **`career_analysis.py:38-40`** — `analysis` が None のとき `logger.error` + `return` の silent return。worker は例外を受け取らないため正常終了として処理し、UI 側で「completed」として誤観測される。
2. **`github_analysis_service.py:35,41`** — `payload["user_id"]` で `KeyError`、cache 不在時に `RuntimeError`。どちらも worker の汎用 `except Exception` 経路でリトライ対象になってしまうが、本質的にはディスパッチ側のバグであり、再試行しても回復しない。

前回 turn で `blog_summarize.py` は同パターンを既に `NonRetryableError` 化済みだったため、3 ハンドラ間で挙動を揃える必要があった。

CLAUDE.md より（再掲）:

> タスクハンドラの「黙って return」は禁止: 失敗パスでは `NonRetryableError` / `RetryableError` を `raise` し、worker に `dead_letter` / `retrying` 遷移と通知発行を任せる。早期 return は呼び出し側に completed として観測される。

## Changes

### `app/services/tasks/handlers/career_analysis.py`

- 必須キー（`user_id` / `record_id` / `target_position`）欠落時に `NonRetryableError` を raise（`missing` リストをメッセージに含める）。
- record 不在時の silent return を `NonRetryableError` raise に置換。
- `payload["..."]` の直接アクセスを `.get()` に統一し、`KeyError` の発生経路を排除。

### `app/services/intelligence/github_analysis_service.py`

- `payload["user_id"]` の `KeyError` → `NonRetryableError`。
- cache 不在時の `RuntimeError` → `NonRetryableError`。

### `backend/tests/services/tasks/test_handlers_failure.py`（新規, 7 ケース）

3 ハンドラの失敗パスを横断的に固定化:

- `TestBlogSummarizeHandlerFailures`: user_id 欠落 / cache 不在
- `TestCareerAnalysisHandlerFailures`: user_id 欠落 / record_id 欠落 / record 不在
- `TestGithubAnalysisHandlerFailures`: user_id 欠落 / cache 不在

すべて `pytest.raises(NonRetryableError)` で明示的に検証（CLAUDE.md「失敗パスを `pytest.raises(ExpectedError)` で必ず assert する」原則）。

### `backend/tests/test_worker_extended.py`（旧契約 assert の更新）

CLAUDE.md「契約変更時は既存テストの assert を必ず見直す。旧契約を固定化したテスト（例: `test_no_cache_returns_early` のような silent-return アサーション）が残ると修正の意図が後退する。テスト名と本体の両方を更新する」原則に従い、以下を改名+書き換え:

- `test_no_cache_raises_runtime_error` → `test_no_cache_raises_non_retryable`
- `test_no_record_returns_early` → `test_no_record_raises_non_retryable`

## TDD フロー

1. **red**: 修正前に `pytest tests/services/tasks/test_handlers_failure.py` で 5/7 失敗（career_analysis 3 / github_analysis 2）。`blog_summarize` 2 件は前回修正済みで pass。
2. **green**: ハンドラ修正後、新規テスト 7/7 pass。
3. 旧契約 assert 2 件を新契約に追従。`make test-backend` 全件 pass。

## Validation

```bash
make lint-backend     # All checks passed
make test-backend     # 503 passed
```

- 個別実行: `nix develop --command bash -c "cd backend && .venv/bin/python -m pytest tests/services/tasks/test_handlers_failure.py -v"` → 7/7 pass
- E2E トリガー外（router / model / migration の変更なし）

## Test plan

- [x] `make test-backend` で全 503 件 pass を確認
- [x] `make lint-backend` clean
- [x] 新規ハンドラ単体テスト 7 件すべて pass
- [x] 旧契約 assert 2 件が新契約で pass
- [ ] stg 環境に Cloud Tasks 経由で不正 payload（user_id 欠落 / 存在しない record_id）を流し、対応するキャッシュレコードが `dead_letter` 状態になることを確認（任意）
- [ ] 失敗時の通知（`failed` ステータス）が `_create_notification` 経由でユーザーに届くことを stg で確認（任意）

## Impact / Risk

- **挙動変更**: 不正な payload を受け取ったタスクは「通知なしの silent completed」ではなく「dead_letter + 失敗通知」になる。ユーザー観測上は **改善**（失敗が見えるようになる）。
- **後方互換**: 公開 API / DB schema / migration の変更なし。
- **リトライ挙動**: `NonRetryableError` は Cloud Tasks のリトライを止めるため、不正 payload で無限リトライしていたケースがあれば即停止する（Cloud Tasks のキュー負荷低減）。

## Out of scope

Backend リファクタリングレビューで挙げた以下は本 PR では未対応（別 PR で順次対応予定）:

- `routers/blog.py` の例外マッピング共通化
- `worker.py` の `_run_*` テスト向けシム削除
- `routers/blog.py` の package 化（accounts / articles / summary）
- `services/blog/collector.py` のプラットフォーム別分割

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
