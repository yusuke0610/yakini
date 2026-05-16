# Frontend Refactor: 責務分離・契約集約・race 防止テストの整備

## Summary

- 3 つの「責務が多すぎる」箇所を hook へ抽出（ProjectModal / useBlogAccountManager / App.tsx）。
- 「進行中ステータス」判定の文字列リテラル 3 箇所を `utils/taskStatus.ts` に集約。
- `api/client.ts` の 401 処理 3 経路を共通ヘルパーにまとめた。
- ログアウト直後の race など、これまでガードできていなかった経路にテストを追加。低価値テストを整理。

## Background

frontend のリファクタリングレビューで次の点を High/Medium として挙げた:

1. **`ProjectModal.tsx` (377 行)** — state + 9 updater + 4 セクション UI が同居。同パターンの `useCareerExperienceMutators` は既に hook 化済みなのに、ProjectModal だけ未適用。
2. **`useBlogAccountManager` (210 行)** — 4 つの per-platform lifecycle（saving / syncing / updating / deleting）を個別 useState で管理。`handleSave` 内に「保存後の自動同期」が直結。
3. **`App.tsx:39-89`** — `setOnUnauthorized` 登録 / `github_error` 展開 / `getCurrentUser` セッション復元 / `justLoggedOut` ref race 防止 の 4 つの useEffect/useRef が同居。**`App.tsx` 自体のテストが存在しない**ため、ログアウト直後の race を回帰検出できない状態だった。
4. **「進行中」ステータス判定の重複** — `pending` / `processing` / `retrying` の or 連鎖が `useAsyncAnalysisPage` / `useCareerAnalysisPage` / `useBlogSummaryPolling` の 3 箇所に複製。契約変更時の修正箇所が分散。
5. **`api/client.ts:126-147`** — 401 → refresh → retry / 401 (refresh 失敗) / `AUTH_EXPIRED` 3 経路で同じ `_onUnauthorized()` + `throw ApiError(AUTH_REQUIRED)` を 3 回書いている。

## Changes

### Step 1: ProjectModal → `useProjectModalForm` 抽出

**新規** `src/hooks/useProjectModalForm.ts`:
- state + 9 updater（`updateField` / `updateTechStack` / `addTechStack` / `removeTechStack` / `updateTeamTotal` / `addTeamMember` / `removeTeamMember` / `updateTeamMember` / `togglePhase`）
- `dateError` 派生値
- `initProject` の純粋関数化

**更新** `src/components/forms/ProjectModal.tsx`: 377 → 236 行（-141 行）。JSX 中心に縮小。

### Step 2: `useBlogAccountManager` の lifecycle 整理

`savingPlatform` / `syncingPlatform` / `updatingPlatform` / `deletingPlatform` を**個別 useState**で持っていた構造を `Partial<Record<PlatformKey, PlatformAction>>` の単一 map に集約:

```ts
type PlatformAction = "saving" | "syncing" | "updating" | "deleting";
const [actions, setActions] = useState<Partial<Record<PlatformKey, PlatformAction>>>({});
const setAction = (platform, action | null) => { ... };
```

外部 API（`savingPlatform` 等の派生値返却）は維持し、消費側の変更不要。

`handleSave` / `handleUpdate` 内の「保存 → 自動同期」連結を `attemptAutoSync(accountId, formatSuccess, fallbackMessage)` ヘルパーに分離（成功時/失敗時のメッセージ整形を渡せる小さな pure な責務）。

### Step 3: `App.tsx` → `useAuthSession` 抽出

**新規** `src/hooks/useAuthSession.ts`: 4 useEffect/useRef を移動。`PUBLIC_PATHS` 判定、`justLoggedOut` ref による race 防止もまとめて担う。

**更新** `src/App.tsx`: 122 → 26 行（-96 行）。`useTheme` + `useAuthSession` の wiring と `<AppRoutes>` のみ。

### Step 4: `utils/taskStatus.ts` 新設

**新規** `src/utils/taskStatus.ts`:

```ts
export type TaskStatus = "pending" | "processing" | "retrying" | "completed" | "dead_letter";
export function isInProgressStatus(status: string | null | undefined): boolean { ... }
```

`useAsyncAnalysisPage` / `useCareerAnalysisPage` / `useBlogSummaryPolling` の 3 箇所から参照差し替え。バックエンド `app/services/tasks/base.py` と同じ判定式。

### Step 5: `api/client.ts` の 401 処理共通化

`buildUnauthorizedError()` ヘルパーを追加し、3 経路の `_onUnauthorized?.()` + `throw new ApiError({ code: "AUTH_REQUIRED", ... })` を 1 箇所に集約。

## Test changes

### 追加（不足分の補填）

| ファイル | ケース | 守る仕様 |
|---|---|---|
| `useDocumentForm.test.ts` | Redux キャッシュ存在時に `loadLatest` が呼ばれない | ページ遷移時の二重 fetch / チラつき防止 |
| `useAsyncAnalysisPage.test.ts` | `fetchProgress` が reject しても polling フェーズが維持される | Redis 障害時に hook 全体が壊れない |
| `useAuthSession.test.ts`（新規, 5 ケース） | sessionStorage 復元 / 公開パス / 保護パスでの復元 / **ログアウト後の race 防止** / handleLoginSuccess | ログアウト直後の `getCurrentUser` 競合を防ぐ（従来 App.tsx でテスト不能だった経路） |
| `useProjectModalForm.test.ts`（新規, 10 ケース） | 初期化 / structuredClone / is_current 切替 / techStack / teamMember / phase / dateError | hook 抽出後の updater ロジック単体テスト |

### 整理（低価値テストの削減）

- `components/analysis/FrameworkList.test.tsx` → `TechBar.test.tsx` にリネーム（実態が TechBar なのにファイル名が乖離していた）。`// items を使ってESLint の unused variable を回避` の dummy assert を撤去。

### レビュー誤検出の訂正

レビュー時に「不足」と挙げた 2 件は **既存テストでカバー済み** だったため追加せず:

- 並列 refresh 抑止 → `api/client.test.ts:71-107` に既存
- `useBlogAccountManager` の sync 失敗 → `useBlogAccountManager.test.ts:160-186` に既存

## Validation

```bash
make lint-frontend       # All checks passed
make test-frontend       # 17 files, 92 tests pass（前回 15 files, 75 tests → +17 ケース）
make build-frontend      # 成功（既存の chunk size warning のみ）
npm run test:e2e         # 13/13 pass（auth / navigation / notifications / github-analysis）
```

App.tsx の認証ライフサイクル変更は CLAUDE.md の E2E トリガー（「認証・ナビゲーション・レイアウトの変更」）に該当するため Playwright も実行済み。

## Test plan

- [x] `make ci` 相当（lint / test / build）すべて pass
- [x] `npm run test:e2e` 13 シナリオすべて pass
- [x] `useAuthSession` race 防止テスト（ログアウト後に `getCurrentUser` が呼ばれない）が新規で追加
- [x] `useProjectModalForm` の 10 updater 分岐がすべてテスト済み
- [ ] ブラウザでの手動確認（任意）:
  - 職務経歴書 → プロジェクト編集モーダルで保存/キャンセル/技術スタック追加削除
  - ブログ連携で zenn / note / qiita の保存 → 自動同期 → 同期失敗時のメッセージ表示
  - ログアウト → 再ログイン直後にちらつきが無いこと

## Impact / Risk

- **挙動変更なし**: すべて内部リファクタリングで、UI / API 通信 / Redux 状態の外部観測動作は維持。
- **追加ガード**: `useAuthSession` テストで race 経路を、`useDocumentForm` テストでキャッシュ復帰経路をそれぞれ守るようになった。今回見つけたわけではないが、潜在的回帰の検知力が上がる。
- **コード行数**: 削除 -352 行 / 追加 +247 行（差し引き -105 行、テスト追加分含む）。

## Out of scope（別 PR で対応予定）

frontend リファクタリングレビューで挙げた以下は本 PR では未対応:

- `hooks/` を `hooks/auth/` `hooks/form/` `hooks/blog/` 等のサブディレクトリへ再編（import 影響が広範のため別 PR）
- `useDocumentForm` 内の Redux キャッシュ wiring を `useFormCache` に分離
- `useCareerAnalysisPage:37` の `pollingId!` non-null assertion 除去
- `GitHubAnalysisPage.tsx` のダッシュボード JSX 87 行を子コンポーネントへ抽出
- `CareerResumeForm.tsx` のヘッダーアクション群を `<CareerResumeFormHeader>` に切り出し
- `pages/GitHubCallbackPage.tsx` を thin wrapper 化（実体を `components/auth/` へ）

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
