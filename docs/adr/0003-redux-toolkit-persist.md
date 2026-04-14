# ADR-0003: Redux Toolkit + redux-persist の採用

## ステータス

Accepted

## コンテキスト

DevForge のフロントエンド（React 18 + TypeScript + Vite）では、ページ間遷移をまたいで保持したいフォーム一時キャッシュが必要だった。

具体的には職務経歴入力フォーム（会社名・在籍期間・業務内容等）の入力途中の状態を、別ページへ遷移して戻った際にも復元したいというユースケースがある。

なお現在のルーティングは React Router による URL ベース管理を採用しており、ページ・パラメータは URL で管理している。

## 決定内容

状態管理ライブラリとして **Redux Toolkit** を採用し、フォーム一時キャッシュの永続化基盤として **redux-persist** を導入する。

**store 構成**:

```
store/
├── index.ts          ← combineReducers({ formCache })
├── formCacheSlice.ts ← 唯一のスライス
└── persistConfig.ts  ← redux-persist 設定
```

**スライス構成**:

| スライス | 用途 |
|---|---|
| `formCache` | フォームの一時キャッシュ（現在は `"career"` キーのみ） |

**状態管理の分担**:

| 状態の種類 | 管理場所 | 理由 |
|---|---|---|
| 認証状態・ユーザー情報 | `App.tsx` の `useState` + `sessionStorage` | タブ内で完結、Redux 不要 |
| フォーム一時キャッシュ | Redux（`formCache`） | ページ間遷移でも保持したい |
| 分析結果・サーバーデータ | 各フックの `useState` + API フェッチ | 永続はサーバー側が持つ |
| 現在のページ・パラメータ | URL（React Router） | ブックマーク・リロード対応 |

**redux-persist の PII 方針**:

`formCache`（職務経歴フォーム）は会社名・在籍期間・業務内容等の PII を含むため、`persistConfig` の `blacklist` に明示的に追加し localStorage への永続化を禁止している。

```typescript
persistConfig = {
  blacklist: ["formCache"],  // PII を含むため localStorage に保存しない
}
```

`persistConfig.ts` のコメントに「新スライス追加時は PII を含むか確認し、含む場合は必ず blacklist に追加すること」と明記し、将来の開発者への運用ルールとして残している。

## 代替案

| 選択肢 | 評価 |
|---|---|
| React Context API | ページ間遷移での状態保持が複雑になるため採用せず。将来のスライス追加時の拡張性も考慮した |
| Zustand | 検討対象に挙げなかった。Redux Toolkit への習熟度を優先した |
| URL パラメータへの状態格納 | フォームの全入力内容を URL に持たせることは現実的でないため却下 |

## トレードオフ・既知のリスク

1. **redux-persist が実質的に dead code**
   - 現時点では唯一のスライス（`formCache`）が `blacklist` に入っているため、永続化対象がゼロ
   - `persistReducer` / `persistStore` / `PersistGate` のボイラープレートのみが残存している
   - 将来スライスを追加して `whitelist` に入れることで初めて機能する「空の器」状態

2. **Zustand 等の軽量ライブラリとの比較検討を省略**
   - Redux Toolkit 以外の選択肢を習熟度の観点から検討しなかった
   - `formCache` 1 スライスのユースケースに対して Redux は構成がやや重い

3. **auth 状態が sessionStorage に直書きされている**
   - 認証状態は Redux ではなく `App.tsx` の `useState` + `sessionStorage` で管理しており、アーキテクチャとして統一されていない

## 将来の移行条件

- 新スライスを追加する際は、PII の有無を確認したうえで `blacklist` / `whitelist` を更新すること
- `formCache` 以外のスライスが増えてきた場合、auth 状態の Redux 移行（`authSlice` の追加）を検討する
- ボイラープレートのコスト感が問題になった場合、Zustand への移行を再検討する

## 関連リンク

- [frontend/src/store/index.ts](../../frontend/src/store/index.ts) — store 構成
- [frontend/src/store/formCacheSlice.ts](../../frontend/src/store/formCacheSlice.ts) — formCache スライス実装
- [frontend/src/store/persistConfig.ts](../../frontend/src/store/persistConfig.ts) — redux-persist 設定・PII 方針
