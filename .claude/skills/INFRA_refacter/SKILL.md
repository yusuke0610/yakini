---
name: INFRA_refacter
description: Use when reviewing or planning refactors for the DevForge infra (OpenTofu, modules/environments), especially HCL duplication across dev/stg/prod, modules 化候補, variable 抽出, environment 差分の整理, oversized resource block, responsibility separation. Trigger on requests such as "infra のリファクタリングを見て", "modules 化候補を出して", "dev/stg/prod の重複を見て", "infra の責務分離", "INFRA_refacter 実行".
---

# Infra Refactor Review (OpenTofu)

DevForge の infra (`infra/modules/` `infra/environments/{dev,stg,prod}`) を対象にした保守性レビュー。

`make dupe-check` の baseline では **HCL の重複率が 21.92% と全領域で最大**。本 skill はそれを構造的に解消する設計提案を出すために使う。

## 先に読む

- `.claude/CLAUDE.md`
- `.claude/rules/infra/opentofu.md`
- `.claude/rules/infra/test.md`
- `.claude/rules/common/duplication.md`（DRY / 重複検知ポリシー）
- `report/dupe/jscpd-report.json`（存在すれば infra 配下の clone を抽出）

## 対象

- `infra/modules/**`
- `infra/environments/**`
- 必要に応じて `flake.nix` の tofu バージョン、`.github/workflows/*.yml` の infra ジョブ、`docs/data-model.md` の Turso セクション

## 成果物の出力先（必須）

- 保存先: `report/INFRA_report_<YYYYMMDD_HHMM>.md`
- 既存の `INFRA_report_*.md` は履歴として残す

### ターミナルへの出力ルール

- レポート本文を assistant メッセージへ貼らない
- ターミナルには以下だけ返す:
  1. 保存先パス
  2. `Verdict` の 3-5 行サマリ
  3. 次に取るべきアクション 1-2 行

## 目的

OpenTofu / Terraform の infra コードでは、「環境差分（dev/stg/prod）を表現するための重複」と「責務未分離による重複」を区別することが本質。本 skill は両者を切り分け、modules 化と variable 抽出の機会を可視化する。

以下を区別する:

- **正当な重複**: `terraform.tfvars` で env 別の値を渡しているだけの構成（HCL 構造は同じ、値だけが違う）
- **責務未分離による重複**: 同じ resource block を 3 環境の `main.tf` にコピペしており、modules 化していれば 1 箇所で済むもの
- **差分が小さい類似 modules**: ほぼ同じ内容の modules が 2 つ以上あり、variable で吸収できるもの
- **不要な variable**: 全環境で同じ値が渡されている variable（環境差分が無いなら module 内ハードコードに戻すか定数化）

## 調査の進め方

### 1. インベントリ

- `rg --files infra/ -t hcl -t terraform 2>/dev/null || find infra -name '*.tf' -o -name '*.tfvars'`
- 各環境の `main.tf` 行数比較: `wc -l infra/environments/{dev,stg,prod}/*.tf`
- modules の使われ方マッピング: `rg -n "^module " infra/environments/`
- variable 一覧と参照状況: `rg -n "^variable " infra/modules/*/variables.tf`、`rg -n "var\.\w+" infra/modules/`

`make dupe-check` の最新レポートから HCL の clone を抽出し、上位 N 件をピックアップする。

### 2. 重複の分類（infra 特有）

- **modules 化候補（High）**: 同じ resource block が 2 環境以上の `environments/<env>/main.tf` に存在
- **variable 抽出候補（High）**: 既存 module の内部で「ほぼ同じだが値だけ違う」設定が分岐している
- **module 統合候補（Medium）**: 2 つの module が ≥ 70% 同じ構造を持つ。差分は variable で吸収可能か検証
- **不要 variable（Low）**: 全環境で同じ値の variable。module 内に固定値として戻す
- **正当な重複（Allowed）**: HCL 構造的に共通、tfvars で env 別値を渡している既存パターン

### 3. 責務未分離の検出

以下のいずれかに当てはまれば責務分離候補:

- 1 つの module が複数の責務（コンピュート + IAM + ネットワーク + モニタリング）を持つ
- `environments/<env>/main.tf` の中で raw な resource ブロックがあり、modules を経由していない
- module 内で `count` / `for_each` を駆使して大きく分岐しており、別 module に分けた方が見通しがよい
- variable がフラットすぎる（`object({ ... })` で構造化すべきものが個別 variable に分解されている）

サイズの目安（補助指標）:

- 単一 module の `main.tf` が 300 行超で責務が複数
- `environments/<env>/main.tf` が 200 行超
- variable が 20 個超で構造化できそう

### 4. 構造変更の提案

提案するときは以下をセットで出す:

- 何が今の重複・責務未分離か（具体的なパスと行）
- どの resource block / variable を modules 化または抽出するか
- 抽出後の `modules/<name>/` の構造（`main.tf` / `variables.tf` / `outputs.tf`）
- environments 側の呼び出し例（`module "<name>" { source = "../../modules/<name>" ... }`）
- 移行時の state 影響（`terraform state mv` が必要なら明記。`prevent_destroy` がついているリソースは特に注意）

### 5. CI / デプロイへの影響

modules を変更すると **全環境の validate が必要**（`.claude/rules/infra/test.md` 参照）。
変更影響として以下を必ず記載する:

- どの環境の validate が必要か（modules 変更 = 全環境）
- `tofu plan` で意図しない差分（特に `-/+` 再作成）が出ないか
- state 移行が必要な場合の手順

## レビューの厳しさ

- 「行が長いから modules 化」ではなく、「変更理由が複数領域に渡るから分割」で判断する
- 「環境ごとにコピペがある」だけで modules 化を断定しない。**正当な環境差分（cloud_run のメモリ・min_instance 等）** は variable で吸収すべきで、modules 化は構造重複に限る
- 「modules 統合できる」は弱い指摘。統合後に variable が爆発するなら現状維持

## 推奨出力フォーマット

下記テンプレートを `report/INFRA_report_<YYYYMMDD_HHMM>.md` に書き込む。

````markdown
# Infra Refactor Review

## Verdict
- infra 保守性の総評を 3-5 行で要約（HCL 重複率、modules 化機会、責務分離の状況）

## Findings
### High
- [infra/environments/<env>/main.tf:line] 何が重複しているか / 責務が混ざっているか。どこに modules 化するか。

### Medium
- ...

### Low
- ...

## Duplication Findings
### Modules 化候補
- [environments/dev/main.tf:line] ↔ [environments/stg/main.tf:line] ↔ [environments/prod/main.tf:line]
  - 抽出先: `infra/modules/<new_name>/`
  - variable 候補: <env 別に異なる値>
  - state 影響: <あり / なし>

### Variable 抽出候補
- [modules/<name>/main.tf:line] ハードコードされている値。variable 化して env から渡す。

### Module 統合候補
- [modules/A] と [modules/B] が ≥ 70% 同構造。差分 X を variable 吸収して統合。

### Allowed Duplication
- [path] 環境差分を tfvars で吸収している正当な重複。記録のみ。

## Structure Review
### Oversized Modules
- [path] 何の責務が混ざっているか。どう切るか。

### Directory Changes
- 提案する target 構成

```text
infra/
  modules/
    cloud_run/
    artifact_registry/
    ...
  environments/
    dev/
    stg/
    prod/
```

## Refactor Plan
1. まずどの resource block を modules 化するか（PR 1）
2. 次にどの variable を抽出 / 統合するか（PR 2）
3. 最後に state 影響を伴う変更を分離（PR 3、`tofu plan` で必ず確認）

## Validation
- `make infra-fmt-check`
- `make infra-validate`
- `make dupe-check`
- `tofu plan` の結果（state 影響がある場合）
````

## 最低限の検証コマンド

- `make infra-fmt-check`
- `make infra-validate`（dev/stg/prod 全環境。modules を触ったら必須）
- `make dupe-check`（重複率 before/after の比較に使う）

実装変更は `INFRA_apply` skill が担う。本 skill はレビューと提案までで止める。
