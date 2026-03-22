## GitHub 運用ルール

### Issue 作成

Issue は `gh` CLI で作成する。テンプレートファイルは使用しない。

#### 機能追加 (feature)

```bash
gh issue create \
  --title "feat: タイトル" \
  --label "feature" \
  --body "$(cat <<'EOF'
## 🧩 Problem

## 🎯 Goal

## 💡 Solution

## 🛠 Scope

- [ ]

## 🚫 Out of Scope

-

## 📊 Impact

- [ ] Frontend
- [ ] Backend
- [ ] Data
EOF
)"
```

#### 改善 (improvement)

```bash
gh issue create \
  --title "improve: タイトル" \
  --label "improvement" \
  --body "$(cat <<'EOF'
## 現状の課題

## 改善内容

## 対応範囲

- [ ]

## 影響範囲

- [ ] Frontend
- [ ] Backend
- [ ] Infra
EOF
)"
```

#### リファクタリング (refactor)

```bash
gh issue create \
  --title "refactor: タイトル" \
  --label "refactor" \
  --body "$(cat <<'EOF'
## リファクタリング対象

## 現状の問題点

## 改善方針

## 対応範囲

- [ ]

## 影響範囲

- [ ] Frontend
- [ ] Backend
- [ ] Infra
EOF
)"
```

#### バグ修正 (bug)

```bash
gh issue create \
  --title "fix: タイトル" \
  --label "bug" \
  --body "$(cat <<'EOF'
## 発生している問題

## 再現手順

## 期待する動作

## 原因（わかれば）

## 影響範囲

- [ ] Frontend
- [ ] Backend
- [ ] Infra
EOF
)"
```

### Pull Request 作成

PR は `gh` CLI で作成する。現在のブランチから自動検出する。

```bash
gh pr create \
  --title "タイトル" \
  --body "$(cat <<'EOF'
## 概要

## 変更内容

-

## 関連 Issue

closes #

## 確認事項

- [ ] CI が通ること
- [ ] 動作確認済み
EOF
)" \
  --base dev
```

- `--base` は原則 `dev` ブランチ
- 関連 Issue がある場合は body 内に `closes #番号` を含める
- label はIssueの種別に合わせて `--label` で付与する

### ラベル管理

リポジトリに以下のラベルが存在しない場合は作成する:

```bash
gh label create feature --color 0E8A16 --description "新機能" --force
gh label create improvement --color 1D76DB --description "改善" --force
gh label create refactor --color D93F0B --description "リファクタリング" --force
gh label create bug --color B60205 --description "バグ修正" --force
```
