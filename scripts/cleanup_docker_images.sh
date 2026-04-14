#!/bin/bash
# Artifact Registry の古い Docker イメージを削除するスクリプト。
#
# Terraform の cleanup_policies と同じ方針を手動実行する:
#   - タグ付きイメージ: UPDATE_TIME 降順で最新 3 件を保持、それ以外を削除
#   - タグなし (untagged) イメージ: 1 日 (86400 秒) 以上経過したものを削除
#
# 対象: 指定リージョンの全 Docker リポジトリ
#
# 使用方法:
#   bash scripts/cleanup_docker_images.sh             # dry-run（確認のみ）
#   bash scripts/cleanup_docker_images.sh --dry-run   # dry-run（明示指定）
#   bash scripts/cleanup_docker_images.sh --execute   # 実際に削除を実行
#
# 依存: gcloud (認証済み), python3

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

KEEP_COUNT=3           # タグ付きイメージの保持件数（Terraform ポリシーと同値）
MAX_AGE_SECS=86400     # untagged 削除までの経過秒数（1 日）
LOCATION="asia-northeast1"

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [[ -z "$PROJECT_ID" ]]; then
  echo "エラー: GCP プロジェクトが設定されていません。" >&2
  echo "  gcloud config set project PROJECT_ID を実行してください。" >&2
  exit 1
fi

if [[ "$DRY_RUN" == "true" ]]; then
  echo "=== DRY-RUN モード: 削除は行いません ==="
else
  echo "=== EXECUTE モード: イメージを実際に削除します ==="
fi

echo "対象プロジェクト: $PROJECT_ID"
echo "対象リージョン  : $LOCATION"
echo ""

# ── ユーティリティ ────────────────────────────────────────────────────

# ISO 8601 タイムスタンプ ("2024-01-15T10:00:00Z" 等) を UNIX エポック秒に変換する。
# macOS (BSD date) と Linux (GNU date) の両方に対応するため python3 を使用する。
to_epoch() {
  python3 -c "
from datetime import datetime, timezone
s = '$1'.replace('Z', '').split('+')[0].split('.')[0]
dt = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
import calendar; print(calendar.timegm(dt.timetuple()))
" 2>/dev/null || echo 0
}

NOW_EPOCH=$(python3 -c "import time; print(int(time.time()))")
CUTOFF_EPOCH=$((NOW_EPOCH - MAX_AGE_SECS))

# ── 全 Docker リポジトリ取得 ──────────────────────────────────────────

repos=$(gcloud artifacts repositories list \
  --project="$PROJECT_ID" \
  --location="$LOCATION" \
  --filter="format=DOCKER" \
  --format="value(name)" \
  2>/dev/null) || {
  echo "エラー: リポジトリ一覧の取得に失敗しました。gcloud の認証を確認してください。" >&2
  exit 1
}

if [[ -z "$repos" ]]; then
  echo "Docker リポジトリが見つかりませんでした。"
  exit 0
fi

total_delete=0

# ── 各リポジトリのイメージを処理 ──────────────────────────────────────

while IFS= read -r repo_full; do
  repo_name="${repo_full##*/}"
  registry="$LOCATION-docker.pkg.dev/$PROJECT_ID/$repo_name"

  echo "─── リポジトリ: $repo_name ($registry) ───────────────────────────────"

  # UPDATE_TIME 降順でイメージ一覧を取得
  # --include-tags: タグ情報を含める（untagged 判定に必要）
  # 1 ダイジェストが複数タグを持つ場合、1 行に TAGS がまとめて返される
  images_raw=$(gcloud artifacts docker images list "$registry" \
    --include-tags \
    --sort-by="~UPDATE_TIME" \
    --format="value(IMAGE,TAGS,DIGEST,UPDATE_TIME)" \
    2>/dev/null) || {
    echo "  警告: イメージ一覧の取得に失敗しました。スキップします。"
    echo ""
    continue
  }

  if [[ -z "$images_raw" ]]; then
    echo "  イメージなし。"
    echo ""
    continue
  fi

  # seen_digests: 処理済みダイジェストをスペース区切りで追跡する（bash 3.2 compat）
  seen_digests=" "
  tagged_kept=0
  repo_delete=()

  while IFS=$'\t' read -r img_path tags digest update_time; do
    [[ -z "$img_path" ]] && continue
    [[ -z "$digest"   ]] && continue

    # 同一ダイジェストの重複行（タグごとに行が分かれるケース）をスキップ
    if echo "$seen_digests" | grep -qF " $digest "; then
      continue
    fi
    seen_digests="$seen_digests$digest "

    short_digest="${digest:0:19}..."

    if [[ -z "$tags" ]]; then
      # ── untagged ──────────────────────────────────────────────────
      img_epoch=$(to_epoch "$update_time")
      if [[ "$img_epoch" -lt "$CUTOFF_EPOCH" ]]; then
        repo_delete+=("$img_path@$digest")
        echo "  削除対象 [untagged, 経過 $(( (NOW_EPOCH - img_epoch) / 3600 ))h]: $short_digest"
      else
        echo "  保持     [untagged, 新しい]: $short_digest"
      fi
    else
      # ── tagged ────────────────────────────────────────────────────
      tagged_kept=$((tagged_kept + 1))
      if [[ "$tagged_kept" -le "$KEEP_COUNT" ]]; then
        echo "  保持     [tagged $tagged_kept/$KEEP_COUNT]: $tags"
      else
        repo_delete+=("$img_path@$digest")
        echo "  削除対象 [tagged, 古い $tagged_kept]: $tags"
      fi
    fi
  done <<< "$images_raw"

  echo "  → 削除対象: ${#repo_delete[@]} 件"
  total_delete=$((total_delete + ${#repo_delete[@]}))

  # 実際の削除（--execute 時のみ）
  if [[ "$DRY_RUN" == "false" ]]; then
    for ref in ${repo_delete[@]+"${repo_delete[@]}"}; do
      echo -n "  delete: $ref ... "
      # --async: 削除完了を待たない（大量削除時のタイムアウト回避）
      if gcloud artifacts docker images delete "$ref" \
          --quiet \
          --async \
          2>/dev/null; then
        echo "受付済み"
      else
        echo "失敗（手動確認が必要）"
      fi
    done
  fi

  echo ""
done <<< "$repos"

# ── サマリ ────────────────────────────────────────────────────────────

echo "======================================="
echo "削除対象イメージ数: $total_delete"

if [[ "$DRY_RUN" == "true" ]]; then
  echo ""
  echo "DRY-RUN モードのため実際の削除は行いませんでした。"
  echo "削除を実行するには以下を実行してください:"
  echo "  bash scripts/cleanup_docker_images.sh --execute"
else
  echo "削除リクエスト送信完了（--async のため完了まで数分かかる場合があります）。"
fi
