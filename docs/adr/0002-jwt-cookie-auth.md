# ADR-0002: JWT + Cookie 認証方式の採用

## ステータス

Accepted

## コンテキスト

DevForge はエンジニア向けキャリア分析ツールであり、ユーザーの職務経歴・資格・GitHub 活動等の PII（個人識別情報）を扱う。

認証方式として以下の要件があった。

- PII をブラウザのストレージに保持したくない
- エンジニア向けサービスのため、GitHub アカウントを前提にできる
- パスワード管理の運用コストを排除したい
- XSS・CSRF の両攻撃に対して防御が必要

当初はメール/パスワード認証を実装していたが、GitHub OAuth only に完全移行し、メール/パスワード認証のコードは削除済み。

## 決定内容

**認証プロバイダ**: GitHub OAuth only

**トークン方式**: JWT（RS256 署名）をバックエンドで発行し、HttpOnly Cookie に格納する。

アクセストークン（有効期限 15 分）とリフレッシュトークン（有効期限 7 日）の 2 種類を発行する。

JWT ペイロードは最小限の構成とし、DB への問い合わせを `sub` クレームの `username` で行う。

```
# アクセストークン
{"sub": username, "type": "access", "exp": <datetime>}

# リフレッシュトークン
{"sub": username, "type": "refresh", "exp": <datetime>}
```

GitHub OAuth ユーザーは `sub` に `"github:<login>"` 形式のプレフィックスを付与することで、通常ユーザーとの競合を回避する。`username` カラムには UNIQUE 制約を設定しているため一意に取得可能。

**Cookie 設定**:

| Cookie名 | HttpOnly | Secure | SameSite | path | JS から読める |
|---|---|---|---|---|---|
| `access_token` | true | 環境変数依存 | 環境変数依存 | `/` | 不可 |
| `refresh_token` | true | 環境変数依存 | 環境変数依存 | `/auth/refresh` | 不可 |
| `csrf_token` | false | 環境変数依存 | strict（固定） | `/` | 可 |

**CSRF 対策**: ダブルサブミット Cookie パターンを採用。

1. ログイン時にバックエンドが `csrf_token` Cookie をセット（JS 読み取り可）
2. フロントが Cookie から `csrf_token` を読み取り、リクエストヘッダ `x-csrf-token` に付与
3. `CSRFMiddleware` が `Cookie の値 == ヘッダの値` を検証

**refresh_token の scope 限定**: `path=/auth/refresh` に限定することで、他の API エンドポイントへのリクエスト時にブラウザが `refresh_token` を送信しない設計とし、漏洩範囲を最小化している。

## 代替案

| 選択肢 | 評価 |
|---|---|
| localStorage への JWT 保存 | PII を扱うサービスのため XSS でトークンが窃取されるリスクを許容できず却下 |
| メール/パスワード認証の継続 | GitHub アカウントを前提にできること・パスワード管理の運用コスト排除を優先し、GitHub OAuth only に移行して削除済み |
| セッション ID 方式（サーバーサイドセッション） | SQLite + min-instances=0 の構成ではセッションストアが揮発するリスクがあるため、ステートレスな JWT 方式を採用 |
| Firestore をセッションストアに利用 | 現フェーズでは構成を増やさない方針のため対象外 |

## トレードオフ・既知のリスク

以下は個人開発フェーズ（〜10 ユーザー）として意図的に許容している既知の設計上の欠陥である。

1. **サーバー側でのトークン失効が不可能**
   - `clear_auth_cookies()` はブラウザの Cookie を削除するのみで、サーバー側でのトークン無効化は行わない
   - ログアウト後も JWT の有効期限が切れるまでトークン自体は有効な状態が続く

2. **`/auth/logout` エンドポイントが未実装**
   - `clear_auth_cookies()` の呼び出し元が存在しない（→ [#181](https://github.com/yusuke0610/devforge/issues/181)）

3. **リフレッシュトークン盗難時のリボーク手段がない**
   - リフレッシュトークンは DB に保存していないため、盗まれた場合は 7 日間サーバー側から無効化できない（→ [#181](https://github.com/yusuke0610/devforge/issues/181)）

4. **XSS が成立すると CSRF 保護が無効化される**
   - ダブルサブミット Cookie パターンは XSS 対策が前提。XSS で `csrf_token` が読まれた場合、CSRF 保護は意味をなさない
   - ただし `access_token` は HttpOnly のため、XSS による JWT 直接窃取は防止できる

## 将来の移行条件

ユーザー数増加またはセキュリティ要件の強化が必要になった場合、以下の対応を検討する。

- `users` テーブルに `refresh_jti`（JWT ID）カラムを追加し、ログアウト時に NULL クリアすることで最小コストのリボーク機能を実装する
- `/auth/logout` エンドポイントを実装する
- リフレッシュトークンローテーションを導入する

## 関連リンク

- [backend/app/core/security/auth.py](../../backend/app/core/security/auth.py) — JWT 発行・検証の実装
- [backend/app/core/security/csrf.py](../../backend/app/core/security/csrf.py) — CSRF ミドルウェアの実装
- [backend/app/routers/auth/token_manager.py](../../backend/app/routers/auth/token_manager.py) — Cookie セット・削除の実装
- [#181](https://github.com/yusuke0610/devforge/issues/181) — リフレッシュトークン失効・ログアウト機能の実装 Issue
