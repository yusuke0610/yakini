---
name: INFRA_apply
description: Use when applying the refactor plan produced by the INFRA_refacter skill. Reads `report/INFRA_report_<timestamp>.md` (latest by default, or a path passed as argument), confirms scope with the user, implements changes against `infra/` (modules 化 / variable 抽出 / module 統合), runs infra-fmt-check / infra-validate / dupe-check, then writes a result report to `report/INFRA_pr_<timestamp>.md`. Trigger on requests such as "INFRA_apply 実行", "infra のリファクタを適用", "INFRA レポートの内容を実装", "modules 化を実装".
---

# Infra Refactor Apply

`INFRA_refacter` skill が生成したレビュー (`report/INFRA_report_*.md`) を入力にして、実際の infra 変更 (modules 化 / variable 抽出 / 統合) と検証、PR 用レポート作成までを行う skill。

## 先に読む

- `.claude/CLAUDE.md`
- `.claude/skills/INFRA_refacter/SKILL.md`（出力フォーマットの参照元）
- `.claude/rules/infra/opentofu.md`
- `.claude/rules/infra/test.md`
- `.claude/rules/common/duplication.md`

## 入力（対象レポートの選択）

引数で明示パスが渡されていればそれを使う。なければ `report/INFRA_report_*.md` の中で最新（mtime 降順）を採用する。

```bash
/INFRA_apply report/INFRA_report_20260516_1042.md
/INFRA_apply
```

最初に必ずユーザーへ「採用したレポートのパス」を 1 行返す。

```text
採用レポート: report/INFRA_report_20260516_1042.md
```

`report/` 配下に `INFRA_report_*.md` が無い場合は停止し、`/INFRA_refacter` の実行を促す。

## 実装スコープの確認（必須）

レポートを読み込んだら、Findings を High / Medium / Low の件数と Modules 化候補 / Variable 抽出候補 / Module 統合候補の件数で集計してユーザーへ提示し、どこまで適用するかを **毎回必ず聞く**。勝手に全件着手してはいけない。

提示例:

```text
採用レポート: report/INFRA_report_20260516_1042.md
Findings: High 2 / Medium 4 / Low 3
Duplication: Modules 化 2 / Variable 抽出 3 / Module 統合 1
Structure: Oversized 1 / Directory 1

どこまで適用しますか？
  1) High のみ
  2) High + Medium
  3) Duplication (Modules 化 / Variable 抽出) も含める
  4) Structure (ディレクトリ変更) も含める
  5) 全部
  6) 個別に選ぶ（番号で指定）
```

`AskUserQuestion` で選ばせるのが望ましい。

## 実装の進め方

1. **タスク化**: 採用した各項目を `TaskCreate` で 1 タスクずつ切る。
2. **小さく分ける**: 「modules 抽出」「variable 化」「環境呼び出し追従」「state 移行」を別タスクにする。
3. **`infra/` のコーディング規約を厳守**:
   - コメント・description は日本語
   - `terraform.tfvars` は Git 管理対象外（`.gitignore` 済み）。env 別値は `*.auto.tfvars.example` 等で例を残す
   - `lifecycle { prevent_destroy = true }` 付きリソースの破壊的変更は禁止
4. **Modules 化**:
   - `infra/modules/<new_name>/{main.tf, variables.tf, outputs.tf}` を作成
   - `environments/<env>/main.tf` の対応する resource を削除し、`module "<new_name>" { source = "../../modules/<new_name>" ... }` に置換
   - 既存リソースを modules 経由に切り替える場合、**state 移行が必要**。`tofu state mv <old> <new>` の手順を Validation セクションに書く
   - state 移行は本番影響あるため、提案時は **PR を分けて apply 担当者に手順を明示** する
5. **Variable 抽出**:
   - module 内のハードコード値を `variable "..." { type = ... default = ... }` で抽出
   - `environments/<env>/main.tf` の module 呼び出しで明示的に渡す
   - 全環境で同じ値なら default を残し env 側で省略可能にする
6. **Module 統合**:
   - 2 module を 1 つに統合する場合、差分は variable で吸収
   - 旧 module ディレクトリは削除し、参照側を一括追従する

## 検証（必須）

実装が一通り終わったら **必ず全環境で validate を回す**。modules を触ったら dev/stg/prod 全て必須（`.claude/rules/infra/test.md`）。

```bash
make infra-fmt-check
make infra-validate          # dev / stg / prod 全環境
make dupe-check              # 重複率 before/after の比較
```

state 影響がある場合は手元で `tofu plan` を回し、意図しない `-/+` 再作成が無いか確認する:

```bash
nix develop --command bash -c "tofu -chdir=infra/environments/dev plan"
nix develop --command bash -c "tofu -chdir=infra/environments/stg plan"
nix develop --command bash -c "tofu -chdir=infra/environments/prod plan"
```

sandbox が `~/.cache/nix/fetcher-locks/*.lock` で落ちる場合は `dangerouslyDisableSandbox: true` で再実行。

validate / plan に意図しない差分があれば、原因を直してから次に進む。`prevent_destroy` 付きリソースの再作成差分は絶対に PR レポートに pass と書かない。

## 成果物の出力先（必須）

- 保存先: `report/INFRA_pr_<YYYYMMDD_HHMM>.md`
- 既存 `INFRA_pr_*.md` は履歴として残す。上書き禁止
- 採用元レポートのパスを冒頭に明記

### ターミナルへの出力ルール

- 詳細はファイルにだけ書く
- ターミナルへ返すのは:
  1. 採用レポートのパス
  2. PR レポートのパス
  3. `Summary` 3-5 行
  4. 検証結果（fmt / validate / plan / dupe-check の pass/fail）
  5. **state 移行手順**（必要な場合は最重要事項として明示）
  6. 残タスク 1-2 行

## PR レポートのフォーマット

````markdown
# Infra Refactor PR Report

- 採用レポート: report/INFRA_report_YYYYMMDD_HHMM.md
- 実装ブランチ: <git branch>
- 適用スコープ: <High のみ / 全部 など>

## Summary
- 何を変えたかを 3-5 行で要約（modules 化件数、variable 抽出件数、重複率の改善）

## Applied Changes
### High
- [infra/...:line] 何を直したか。元レポートの指摘番号や見出しを引用。

### Medium / Low
- ...

## Modules / Variable Changes
### Modules 化
- 新規 modules: `infra/modules/<name>/`
- 置換した resource: [environments/<env>/main.tf:line]

### Variable 抽出
- [modules/<name>/variables.tf] 追加した variable と用途

### Module 統合
- 統合元: [modules/A], [modules/B]
- 統合後: [modules/<merged>]

## Structure Changes
- 変更前 / 変更後のディレクトリ構成（変更があった場合のみ）

```text
infra/
  modules/
    ...
  environments/
    ...
```

## State Migration
- **state 移行が必要な変更がある場合は必ずここに手順を明記**
- 例:
  ```bash
  tofu -chdir=infra/environments/dev state mv \
    google_cloud_run_service.app module.cloud_run.google_cloud_run_service.app
  ```
- 移行担当者の確認事項（apply タイミング、ロールバック手順）

## Skipped
- 採用しなかった指摘と理由

## Validation
- `make infra-fmt-check`: pass / fail
- `make infra-validate`: pass / fail（各環境の結果）
- `tofu plan` (各環境): 差分要約。意図しない再作成があれば抜粋
- `make dupe-check`: 重複率 before / after（特に HCL の %）

## Follow-ups
- 次の PR で対応すべき項目（state 移行 PR の分割、別 modules 化など）
````

## 進め方の流れ（チェックリスト）

1. 採用レポートを決定し、パスをユーザーへ提示
2. Findings 集計を提示し、`AskUserQuestion` で適用スコープを選ばせる
3. 採用項目を `TaskCreate` で 1 つずつ切る
4. 各タスクを `in_progress` にして実装、終わったら `completed`
5. `make infra-fmt-check` / `make infra-validate` / `make dupe-check` を回す
6. state 影響があれば `tofu plan` で各環境確認
7. fail / 意図しない差分があれば直す。pass まで PR レポートを書かない
8. `report/INFRA_pr_<YYYYMMDD_HHMM>.md` を書く
9. ターミナルにはパス・サマリ・state 移行手順を返す
