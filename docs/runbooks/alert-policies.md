# アラートポリシー Runbook

DevForge の不正アクセス検知・自動遮断・通知の運用手順をまとめる。

## 概要

| 監視対象 | 検知層 | 通知層 |
| --- | --- | --- |
| 認証失敗の急増（ブルートフォース） | `devforge/auth_failed`（ログベース指標） | `DevForge Auth Failed Surge`（メール） |
| レートリミット超過の連発 | `devforge/rate_limit_exceeded`（ログベース指標） | `DevForge Rate Limit Surge`（メール） |
| API ヘルスチェック失敗 | `monitoring.googleapis.com/uptime_check/check_passed` | `DevForge API Down`（メール） |
| 非同期タスク失敗 | `devforge/task_failed` | `DevForge Task Failed`（メール） |

通知チャンネルは `google_monitoring_notification_channel.email` を全アラートで共通利用する。
通知先は環境ごとの `infra/environments/{dev,stg,prod}/terraform.tfvars` の `alert_email` 変数で指定する。

## 検知パイプライン

```
FastAPI アプリ
   │ log_event(WARNING, "auth_failed", reason=...)
   │ logger.warning("rate_limit_exceeded", ...)
   ▼
stdout (JSON)
   ▼
Cloud Logging
   │ ログベース指標（フィルタ集計）
   ▼
Cloud Monitoring（アラートポリシー）
   │ 閾値超過で発火
   ▼
Notification Channel (Email)
   ▼
運用者の受信トレイ
```

## 各アラートの仕様

### 1. DevForge Auth Failed Surge

- **目的**: ブルートフォース攻撃や不正なトークン利用の急増を検知する。
- **Log-based Metric**: `devforge/auth_failed`
  - フィルター
    ```
    resource.type="cloud_run_revision"
    severity="WARNING"
    jsonPayload.message="auth_failed"
    ```
  - ラベル `reason`: `EXTRACT(jsonPayload.reason)` で抽出
    - `missing_cookie` / `jwt_decode_error` / `access_wrong_type` / `access_missing_sub` / `refresh_wrong_type` / `refresh_missing_sub` / `refresh_missing_jti` / `user_not_found`
- **発火条件**: 5 分窓（`alignment_period = 300s`）で COUNT が 1,000 を超え、その状態が 60 秒持続したとき。
- **自動クローズ**: 30 分で自動解消。
- **想定誤検知**: 期限切れトークンの再ログイン、フロントエンドのバグによるリトライ。閾値はこれらを許容する余裕を持たせている。

### 2. DevForge Rate Limit Surge

- **目的**: slowapi が 429 を返している状態を検知する（攻撃が自動遮断されているサイン）。
- **Log-based Metric**: `devforge/rate_limit_exceeded`
  - フィルター
    ```
    resource.type="cloud_run_revision"
    severity="WARNING"
    jsonPayload.message="rate_limit_exceeded"
    ```
- **発火条件**: 5 分窓で 500 件超過、60 秒持続。
- **意味**: アプリ側でブロック済みのため緊急性は Auth Failed Surge より低いが、攻撃が継続中であることを示すので無視してはいけない。

## アラート発火時の初動

### Auth Failed Surge を受信した場合

1. **Cloud Logging で攻撃の全体像を確認**
   - GCP Console → Logging → Logs Explorer
   - クエリ:
     ```
     resource.type="cloud_run_revision"
     jsonPayload.message="auth_failed"
     timestamp >= "<アラート発火時刻 - 10分>"
     ```
2. **攻撃元 IP を特定**
   - Logs Explorer のサマリーで `jsonPayload.client_ip` フィールドをフィールドエクスプローラに追加し、件数で降順ソート。
   - 上位の IP がブルートフォース元の可能性が高い。
3. **狙われているエンドポイントを特定**
   - `jsonPayload.path` で集計。`/auth/me` / `/auth/refresh` への大量試行ならクレデンシャル攻撃。
4. **失敗理由の傾向を確認**
   - `jsonPayload.reason` で集計。
     - `jwt_decode_error` 多発 → 改ざんトークンによる総当たり
     - `user_not_found` 多発 → ユーザー名の列挙試行
     - `missing_cookie` 多発 → スキャナによるクローリング
5. **必要に応じて遮断**
   - 同一 IP からの攻撃が継続する場合、GCP Armor の IP ブロックルールまたは Cloud Run の ingress 制限を検討する。
   - 短期遮断: `gcloud compute security-policies rules create` で該当 IP を deny。
6. **インシデント記録**
   - 攻撃時間帯・IP・件数・対応内容を `docs/incidents/` に記録（必要な場合）。

### Rate Limit Surge を受信した場合

1. アプリは正常にブロックしているため、まず深呼吸する。
2. Auth Failed Surge と同じ手順で攻撃元 IP を特定。
3. 攻撃が長時間継続するなら GCP Armor で恒久ブロック。

## 閾値チューニング指針

- **誤検知が多い場合**
  - `auth_failed` の `threshold_value = 1000` を上げる（例: 2,000）。
  - 期限切れの再ログインで起こる`jwt_decode_error` を `reason` ラベルで除外したフィルタに変更することも検討。
- **検知が遅すぎる場合**
  - `alignment_period` を 300s → 60s に短縮し、閾値を比例縮小。
  - ただし瞬間スパイクで誤検知しやすくなる。

## 通知チャンネルの保守

- **メールアドレスの変更**: `infra/environments/{env}/terraform.tfvars` の `alert_email` を更新し `terraform apply`。
- **退職対応**: 個人アドレスは避け、ML（mailing list）を使う運用を推奨。
- **疎通確認**: GCP Console → Monitoring → Alerting → Notification channels → 「Send Test Notification」。

## 関連ファイル

- 認証失敗ログ出力: `backend/app/core/security/auth.py` の `_raise_auth_failed`
- レートリミット 429 ハンドラ: `backend/app/main.py` の `_rate_limit_handler`
- レートリミット定義: `backend/app/core/security/dependencies.py` の `limiter`
- Terraform 定義: `infra/modules/monitoring/main.tf`
- 通知チャンネル変数: `infra/modules/monitoring/variables.tf` の `alert_email`
