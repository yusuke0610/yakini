# Ollama + Qwen2.5 セットアップガイド

DevForge の GitHub 分析機能では、分析結果の自然言語要約に Ollama（ローカル LLM ランタイム）と Qwen2.5 モデルを使用します。
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

## Qwen2.5 モデルのダウンロード

```bash
# 7B パラメータモデル（推奨、約4.7GB）
ollama pull qwen2.5:7b

# 軽量版（3B、メモリが少ない場合）
ollama pull qwen2.5:3b
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
  "model": "qwen2.5:7b",
  "prompt": "Hello",
  "stream": false
}' | python3 -m json.tool
```

## DevForge との連携設定

以下の環境変数で設定をカスタマイズできます（いずれもオプション）:

| 環境変数 | デフォルト値 | 説明 |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama サーバーの URL |
| `OLLAMA_MODEL` | `qwen2.5:7b` | 使用するモデル名 |

## トラブルシューティング

### Ollama が起動しない

```bash
# ポートが使用中の場合
lsof -i :11434

# ログを確認
ollama serve 2>&1
```

### モデルのダウンロードが遅い

Qwen2.5:7b は約 4.7GB です。ネットワーク環境によっては時間がかかります。

### メモリ不足

7B モデルには約 8GB の RAM が必要です。メモリが不足する場合は 3B モデルを使用してください:

```bash
ollama pull qwen2.5:3b
```

環境変数で切り替え:

```bash
export OLLAMA_MODEL=qwen2.5:3b
```

### DevForge で AI 要約が表示されない

1. `ollama serve` が起動しているか確認
2. `curl http://localhost:11434/api/tags` で応答があるか確認
3. 指定したモデルがダウンロード済みか確認
4. バックエンドのログに `Ollama is not available` と出ていないか確認

AI 要約は Ollama が利用できない場合、自動的にスキップされます（エラーにはなりません）。
