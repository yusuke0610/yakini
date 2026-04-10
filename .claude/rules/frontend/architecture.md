---
paths:
  - frontend/**
---

# Frontend アーキテクチャ (React 18 + Vite + TypeScript)

```
frontend/src/
├── router/
│   ├── routes.tsx       # 全ルート定義（パス↔ページ対応表）
│   └── guards.tsx       # PrivateRoute / PublicRoute（Outlet パターン）
├── pages/               # ルートのエントリーポイント（薄いラッパー）
├── components/
│   ├── AuthenticatedLayout.tsx  # サイドバー + <Outlet />（フッターに NotificationBell を配置）
│   ├── LoadingOverlay.tsx       # 共通ローディング UI（position:fixed; z-index:100 でビューポート全体を覆う）
│   ├── NotificationBell.tsx     # 通知ベル（未読バッジ・ドロップダウンパネル）
│   ├── NotificationBell.module.css
│   ├── forms/           # BasicInfoForm, CareerResumeForm, ResumeForm
│   ├── analysis/        # GitHubAnalysisPage, LanguageBar
│   ├── auth/            # LoginForm, RegisterForm
│   └── blog/            # BlogPage
├── hooks/
│   ├── useDocumentForm.ts    # フォーム CRUD の共通フック（loading / saving / error 管理）
│   ├── useMasterData.ts      # マスタデータのモジュールレベルキャッシュ
│   ├── useNotifications.ts   # 通知ベル用フック（30秒ポーリング・パネル開閉・既読処理）
│   └── usePdfActions.ts      # PDF ダウンロード/プレビュー
├── api/
│   ├── client.ts        # fetch ラッパー（Cookie 認証、401 ハンドリング）
│   └── *.ts             # ドメイン別 API モジュール
├── App.tsx              # 認証ステート管理 + <AppRoutes /> 呼び出し
└── main.tsx             # BrowserRouter ラップ
```

**ルーティング**: react-router-dom v7。ガードは Outlet パターン（レイアウトルート）で実装。`/login`, `/signin` は PublicRoute、他は PrivateRoute でガード。

**フォームパターン**: `useDocumentForm` フックが load/create/update/loading/saving を一元管理。各フォームはこのフックを使い、`LoadingOverlay` でデータ取得中の操作をブロックする。
