---
name: frontend_refacter
description: Use when reviewing or planning refactors for the DevForge React frontend, especially for maintainability, redundant or missing unit tests, oversized components or hooks, responsibility separation, and directory structure changes. Trigger on requests such as “frontend のリファクタリングを見て”, “保守性を確認”, “不要な単体テスト”, “単体テストは十分か”, “責務分離”, or “構成見直し”.
---

# Frontend Refactor Review

## 先に読む

- `.claude/CLAUDE.md`
- `.claude/rules/frontend/architecture.md`
- `.claude/rules/frontend/typescript.md`

必要に応じて backend 側 API 契約も確認すること。

## 対象

- `frontend/src/**`
- `frontend/tests/**`
- 必要に応じて `frontend/package.json`, `frontend/vite.config.ts`, `frontend/eslint.config.js`

## 目的

この skill の目的は、React/TypeScript の保守性を「見た目」ではなく、責務分離、状態管理、テスト価値、構成の探索容易性で評価することです。

以下を明確に区別してください。

- 表示ロジックの複雑さ
- データ取得や保存フローの複雑さ
- 再利用可能な hook へ切り出すべき責務
- 低価値テストと不足テスト
- ページ、components、hooks、api の境界不備

## 調査の進め方

### 1. インベントリ

- `rg --files frontend/src frontend/tests`
- 大きいファイルを洗う: `rg --files frontend/src frontend/tests | xargs wc -l | sort -nr | head -n 30`
- まず以下の層で把握する
  - pages: ルート入口。薄いラッパーであるべき
  - components: 表示と局所状態
  - hooks: 再利用可能な非表示ロジック
  - api: fetch と HTTP 変換
  - payload builder / mapper: 純粋関数

### 2. 保守性レビュー

以下に当てはまれば責務分離候補です。

- 1 component が data fetch、mutation、derived state、modal 制御、描画を全部持つ
- 1 hook が API 通信、フォーム状態、画面文言、UI 制御を全部持つ
- page が薄い wrapper ではなく実質的な feature component になっている
- `api/` にエラーマッピングや認証再試行以外の画面知識が入っている
- `components/` 間で props drilling が深く、state ownership が曖昧

サイズの目安は補助指標です。

- component が 250 行超で責務が複数ある
- hook が 180 行超で複数の state machine を持つ
- file 内の `useState` / `useEffect` が多く、表示以外の判断が散在する
- 同一画面向けの helper が component 本体に埋まり、再利用不能になっている

### 3. 単体テストレビュー

不要と判定する条件:

- static markup や単純な props passthrough しか見ていない
- 実装詳細の state 更新順や内部関数呼び出しだけに依存している
- snapshot が多いのに仕様保護よりノイズが大きい
- TypeScript の型が守る内容を冗長に runtime test している
- 同じ payload 変換や同じ分岐を複数テストが重複している

不足と判定する観点:

- form の load/create/update 失敗時
- API エラー文言、401 refresh、再認証導線
- route guard や認証状態に応じた画面分岐
- payload builder / mapper の境界値
- modal、confirm、preview、download の状態遷移
- AI 分析や同期の loading / success / error 分岐
- 複数 hook や API 呼び出しが絡む画面の統合的な振る舞い

不要テストを挙げるときは、必ず「削っても残る保護」を書くこと。  
不足テストを挙げるときは、必ず「何の仕様を守るためのテストか」を書くこと。

### 4. ディレクトリ構成レビュー

以下を確認します。

- `pages/` が本当に薄いか
- `components/` が feature 単位でまとまっているか
- `hooks/` が generic hook と feature hook で混ざっていないか
- `api/`, `types`, `payloadBuilders`, `formMappers` の責務境界が適切か
- CSS Module が component 境界と一緒に保守しやすく配置されているか

構成変更を提案するときは、以下をセットで出してください。

- どの探索コストが高いか
- どの責務をどこへ移すか
- 画面単位か共通部品か
- 過剰抽象化にならない理由

## レビューの厳しさ

- 「長い component」は即分割ではない。状態と責務の分離可能性で判断する
- 「テストが少ない」は弱い指摘。ユーザー影響の大きい分岐が無防備かで判断する
- 「hooks に出せる」は弱い。再利用性か可読性が本当に上がるかまで示す

## 推奨出力フォーマット

````markdown
# Frontend Refactor Review

## Verdict
- 保守性の総評を 3-5 行で要約

## Findings
### High
- [path/to/file.tsx:line] 問題点。なぜ保守性を落とすか。どこへ分けるか。

### Medium
- ...

### Low
- ...

## Test Review
### Remove or Merge
- [path] なぜ低価値か。削除しても何が守られるか。

### Add
- [path or feature] どのユーザー挙動を守るテストか。

## Structure Review
### Oversized Components or Hooks
- [path] 何の責務が混ざっているか。どう切るか。

### Directory Changes
- 提案する target 構成

```text
frontend/src/
  pages/
  features/
  components/
  hooks/
  api/
  ...
```

## Refactor Plan
1. まずどの画面・hook を分解するか
2. どのテストを整理・追加するか
3. 最後にどの確認を回すか

## Validation
- 実行したコマンド
- 未実行ならその理由
````

## 最低限の検証コマンド

- `cd frontend && npm run lint`
- `cd frontend && npm test`
- `cd frontend && npm run build`

コード変更を含む場合は、少なくとも影響範囲の画面とテストを確認し、最後に build まで通してください。
