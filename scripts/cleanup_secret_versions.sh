#!/bin/bash
# Secret Manager の古いバージョンを削除するスクリプト。
#
# 各シークレットに対して以下を実行する:
#   - ENABLED 状態のバージョン: 最新 1 件を残し、それ以外を destroy
#   - DISABLED 状態のバージョン: 全て destroy
#
# デフォルトは dry-run モード（実際の削除は行わない）。
# 本番実行時は --dry-run フラグを外すこと。
#
# 使用方法:
#   bash scripts/cleanup_secret_versions.sh             # dry-run（確認のみ）
#   bash scripts/cleanup_secret_versions.sh --dry-run   # dry-run（明示指定）
#   bash scripts/cleanup_secret_versions.sh --execute   # 実際に削除を実行

set -euo pipefail

# ── 引数処理 ──────────────────────────────────────────────────────────

DRY_RUN=true

for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=true
      ;;
    --execute)
      DRY_RUN=false
      ;;
    *)
      echo "不明なオプション: $arg" >&2
      echo "使用方法: $0 [--dry-run|--execute]" >&2
      exit 1
      ;;
  esac
done

# ── 設定 ──────────────────────────────────────────────────────────────

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [[ -z "$PROJECT_ID" ]]; then
  echo "エラー: GCP プロジェクトが設定されていません。" >&2
  echo "  gcloud config set project PROJECT_ID を実行してください。" >&2
  exit 1
fi

if [[ "$DRY_RUN" == "true" ]]; then
  echo "=== DRY-RUN モード: 削除は行いません ==="
else
  echo "=== EXECUTE モード: バージョンを実際に削除します ==="
fi

echo "対象プロジェクト: $PROJECT_ID"
echo ""

# ── 全シークレット取得 ────────────────────────────────────────────────

secrets=$(gcloud secrets list \
  --project="$PROJECT_ID" \
  --format="value(name)" \
  2>/dev/null)

if [[ -z "$secrets" ]]; then
  echo "シークレットが見つかりませんでした。"
  exit 0
fi

total_destroy=0

# ── 各シークレットのバージョンを処理 ──────────────────────────────────

while IFS= read -r secret_full; do
  # secret_full 例: projects/PROJECT_ID/secrets/SECRET_NAME
  secret_name="${secret_full##*/}"

  echo "─── シークレット: $secret_name ───────────────────────────────"

  # バージョン一覧を取得（バージョン番号の降順で取得）
  versions=$(gcloud secrets versions list "$secret_name" \
    --project="$PROJECT_ID" \
    --format="value(name,state)" \
    --sort-by="~name" \
    2>/dev/null) || {
    echo "  警告: バージョン一覧の取得に失敗しました。スキップします。"
    continue
  }

  if [[ -z "$versions" ]]; then
    echo "  バージョンなし。スキップします。"
    continue
  fi

  # ENABLED バージョンを収集（降順ソート済み）
  enabled_versions=()
  disabled_versions=()

  while IFS=$'\t' read -r ver_full state; do
    [[ -z "$ver_full" ]] && continue
    ver_num="${ver_full##*/}"
    case "$state" in
      ENABLED)  enabled_versions+=("$ver_num") ;;
      DISABLED) disabled_versions+=("$ver_num") ;;
      # DESTROYED はスキップ
    esac
  done <<< "$versions"

  # ENABLED: 最新 1 件（配列先頭）を保持、残りを destroy
  keep_version=""
  destroy_enabled=()

  if [[ ${#enabled_versions[@]} -gt 0 ]]; then
    keep_version="${enabled_versions[0]}"
    echo "  ENABLED（保持）: バージョン $keep_version"
    for ver in "${enabled_versions[@]:1}"; do
      destroy_enabled+=("$ver")
      echo "  ENABLED（削除対象）: バージョン $ver"
    done
  fi

  # DISABLED: 全て destroy
  for ver in "${disabled_versions[@]}"; do
    echo "  DISABLED（削除対象）: バージョン $ver"
  done

  all_destroy=("${destroy_enabled[@]}" "${disabled_versions[@]}")
  total_destroy=$((total_destroy + ${#all_destroy[@]}))

  if [[ ${#all_destroy[@]} -eq 0 ]]; then
    echo "  → 削除対象バージョンなし。"
    continue
  fi

  # 実際の削除（--execute 時のみ）
  if [[ "$DRY_RUN" == "false" ]]; then
    for ver in "${all_destroy[@]}"; do
      echo -n "  destroy: バージョン $ver ... "
      if gcloud secrets versions destroy "$ver" \
          --secret="$secret_name" \
          --project="$PROJECT_ID" \
          --quiet \
          2>/dev/null; then
        echo "完了"
      else
        echo "失敗（手動確認が必要）"
      fi
    done
  fi

  echo ""
done <<< "$secrets"

# ── サマリ ────────────────────────────────────────────────────────────

echo "======================================="
echo "削除対象バージョン数: $total_destroy"

if [[ "$DRY_RUN" == "true" ]]; then
  echo ""
  echo "DRY-RUN モードのため実際の削除は行いませんでした。"
  echo "削除を実行するには以下を実行してください:"
  echo "  bash scripts/cleanup_secret_versions.sh --execute"
else
  echo "削除完了。"
fi
