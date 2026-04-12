# Ollama + Gemma 3 セットアップガイド

DevForge の GitHub 分析・キャリアパス分析機能では、分析結果の自然言語要約に Ollama（ローカル LLM ランタイム）と Gemma 3 モデルを使用します。
Ollama はオプション機能であり、起動していなくても分析自体は正常に動作します。

## Ollama とは

[Ollama](https://ollama.com/) はローカルマシン上で大規模言語モデル（LLM）を実行するためのツールです。
API サーバーとして動作し、DevForge のバックエンドから HTTP 経由で呼び出します。

## インストール（macOS）

```bash
# Homebrew
brew install ollama

# または公式サイトからダウンロード
# https://ollama.com/download
```

## Gemma 3 モデルのダウンロード

```bash
# 4B パラメータモデル（推奨、RAM 8GB 以上で動作）
ollama pull gemma3:4b
```

> **モデル選択について**
> - `gemma3:4b`（デフォルト）: RAM ~4 GiB。Docker 環境でも快適に動作。
> - `gemma3:9b`: RAM ~6 GiB。品質向上、やや遅い。
> - `gemma3:27b`: RAM ~18 GiB。高品質だが、ホスト上で Ollama を直接起動する必要あり。

## Ollama サーバーの起動

```bash
ollama serve
```

デフォルトで `http://localhost:11434` でリッスンします。

## 動作確認

```bash
# サーバーの応答確認
curl http://localhost:11434/api/tags

# モデルの動作確認
curl -s http://localhost:11434/api/generate -d '{
  "model": "gemma3:4b",
  "prompt": "Hello",
  "stream": false
}' | python3 -m json.tool
```

## DevForge との連携設定

以下の環境変数で設定をカスタマイズできます（いずれもオプション）:

| 環境変数 | デフォルト値 | 説明 |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama サーバーの URL |
| `OLLAMA_MODEL` | `gemma3:4b` | 使用するモデル名 |
| `OLLAMA_TIMEOUT` | `300.0` | 生成リクエストのタイムアウト秒数 |

## Docker で実行する場合

`docker-compose.yml` に Ollama サービスが含まれており、`gemma3:4b` を自動的に pull・起動します。

```bash
docker compose up
```

コンテナ起動時にモデルの pull が完了してから API サーバーが起動します（初回のみ時間がかかります）。

### メモリ要件

| モデル | 必要メモリ | Docker Desktop 推奨設定 |
|---|---|---|
| `gemma3:4b` | ~4 GiB | 8 GiB 以上 |
| `gemma3:9b` | ~6 GiB | 10 GiB 以上 |

## トラブルシューティング

### Ollama が起動しない

```bash
# ポートが使用中の場合
lsof -i :11434

# ログを確認
ollama serve 2>&1
```

### モデルのダウンロードが遅い

初回 pull 時のみ時間がかかります。`gemma3:4b` は約 2.5 GB のダウンロードです。

### DevForge で AI 要約が表示されない

1. `ollama serve` が起動しているか確認
2. `curl http://localhost:11434/api/tags` で応答があるか確認
3. 指定したモデルがダウンロード済みか確認（`models` 配列に表示されること）
4. バックエンドのログにタイムアウトや接続失敗が出ていないか確認

AI 要約は Ollama が利用できない場合、自動的にスキップされます（エラーにはなりません）。
