# Ollama + Gemma 4 セットアップガイド

DevForge の GitHub 分析機能では、分析結果の自然言語要約に Ollama（ローカル LLM ランタイム）と Gemma 4 モデルを使用します。
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

## Gemma 4 モデルのダウンロード

```bash
# 31B パラメータモデル（推奨、VRAM 20GB以上を推奨）
ollama pull gemma4:31b

# 軽量版が必要な場合は、より小さなパラメータモデル（9B等）を検討してください
```

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
  "model": "gemma4:31b",
  "prompt": "Hello",
  "stream": false
}' | python3 -m json.tool
```

## DevForge との連携設定

以下の環境変数で設定をカスタマイズできます（いずれもオプション）:

| 環境変数 | デフォルト値 | 説明 |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama サーバーの URL |
| `OLLAMA_MODEL` | `gemma4:31b` | 使用するモデル名 |
| `OLLAMA_TIMEOUT` | `1200.0` | 生成リクエストのタイムアウト秒数 |

## トラブルシューティング

### Ollama が起動しない

```bash
# ポートが使用中の場合
lsof -i :11434

# ログを確認
ollama serve 2>&1
```

### モデルのダウンロードが遅い

Gemma 4:31b はサイズが大きいため、ネットワーク環境によっては時間がかかります。

### メモリ不足

31B モデルには約 20GB 以上の VRAM / RAM が必要です。

```bash
ollama pull gemma4:31b
```

環境変数で切り替え:

```bash
export OLLAMA_MODEL=gemma4:31b
export OLLAMA_TIMEOUT=1200.0
```

### DevForge で AI 要約が表示されない

1. `ollama serve` が起動しているか確認
2. `curl http://localhost:11434/api/tags` で応答があるか確認
3. 指定したモデルがダウンロード済みか確認
4. 初回生成だけ遅い場合は、`OLLAMA_TIMEOUT` を増やす
5. バックエンドのログにタイムアウトや接続失敗が出ていないか確認

AI 要約は Ollama が利用できない場合、自動的にスキップされます（エラーにはなりません）。

