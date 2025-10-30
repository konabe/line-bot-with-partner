# LINE Bot with Partner 仕様書

最終更新: 2025-10-27

## 概要
- 本アプリケーションは LINE Messaging API を利用したチャットボットです。
- コマンド検出により、以下の機能を提供します。
  - 「天気」クエリ解析（例: 「東京の天気」）
  - 「じゃんけん」テンプレート送信
  - 「今日のご飯」ChatGPT からの提案
  - 「ポケモン」ランダム図鑑（TemplateMessage）
  - 「ぐんまちゃん、」で始まるテキストは ChatGPT による応答
- 起動時に管理者へ通知（任意）。
- Gunicorn を前提に運用します。

## システム構成（アーキテクチャ）
- 言語/ランタイム: Python 3.x + Flask
- Webサーバ: Gunicorn（`start.sh` で起動）
- アーキテクチャ: レイヤード/DDD志向
  - application 層: ルーティング、ハンドラ（`src/application`）
  - domain 層: ドメインロジック（`src/domain`）
  - infrastructure 層: 外部サービス、ポート/アダプタ（`src/infrastructure`）
  - ports: ポート定義（`src/ports`）
- 主要ファイル
  - `src/app.py`: Flask アプリの初期化、ハンドラ登録、起動通知（インポート時一度のみ）
  - `src/application/register_flask_routes.py`: `/health`, `/callback` エンドポイント
  - `src/application/message_handlers.py`: テキストメッセージのコマンド判定と処理
  - `src/application/handler_registration.py`: ハンドラの DI 構成
  - `src/application/startup_notify.py`: 起動通知ヘルパ
  - `src/infrastructure/adapters/line_adapter.py`: LINE Messaging API アダプタ
  - `src/infrastructure/line_model/zukan_flex.py`: ポケモン図鑑の Flex バブル生成
  - `src/infrastructure/adapters/openai_adapter.py`: OpenAI クライアント（`OpenAIAdapter`）
  - `src/infrastructure/logger.py`: DI 可能なロガー

## 外部サービス・依存
- LINE Messaging API v3
  - Webhook 署名検証
  - Reply/Push メッセージ送信
  - TemplateMessage（ButtonsTemplate など）
- OpenAI Chat Completions API
  - エンドポイント: `https://api.openai.com/v1/chat/completions`
  - 通常応答、食事提案
  - リクエストパラメータ: `messages`, `max_completion_tokens`
- PokeAPI（`_get_random_pokemon_zukan_info`）
  - ランダムなポケモン情報取得
- 天気情報
  - `infrastructure/adapters/weather_adapter.py`（実装に依存）

## エンドポイント
- `GET /health`
  - 健康チェック。200/OK を返す。
- `POST /callback`
  - LINE Webhook 受信。
  - 署名検証失敗: 400。
  - ハンドラ内エラー: ログ出力＋可能な限り安全に返信。

## メッセージ処理（コマンドと挙動）
`src/application/message_handlers.py` の `MessageHandler.handle_message` が判定。
- 天気: テキストに「天気」を含む
  - 「◯◯の天気」から地名抽出。なければ東京で応答。
- じゃんけん: 完全一致「じゃんけん」
  - ボタンテンプレートを返信。
- 今日のご飯: 完全一致「今日のご飯」
  - ChatGPT の提案を返信（失敗時は案内メッセージ）。
- ポケモン: 完全一致「ポケモン」
  - ランダムなポケモンの図鑑を TemplateMessage で返信。
- ぐんまちゃん: 「ぐんまちゃん、」で始まるテキスト
  - ChatGPT による通常応答。

## 起動通知
- 実行タイミング: Gunicorn でアプリが import された直後（`src/app.py`）。
- 重複防止: `/tmp/line-bot-startup-notified` の存在でガード（1 コンテナ 1 回）。
- 送信条件: `ADMIN_USER_ID` が設定されている場合のみ。
- メッセージ: `ADMIN_STARTUP_MESSAGE`（未設定時は「サーバーが起動しました。」）。

## 環境変数
- LINE
  - `LINE_CHANNEL_SECRET`: Webhook 署名検証に使用。
  - `LINE_CHANNEL_ACCESS_TOKEN`: Messaging API 呼び出しに使用。
- OpenAI
  - `OPENAI_API_KEY`: 必須。
  - `OPENAI_MODEL`: 省略可（デフォルト `gpt-5-mini`）。
- 起動通知
  - `ADMIN_USER_ID`: 起動通知の送信先。未設定時はスキップ。
  - `ADMIN_STARTUP_MESSAGE`: 通知文（省略可）。
- サーバ
  - `PORT`: リッスンポート（render.yaml では 8080 を想定）。
  - `WORKERS`, `THREADS`, `TIMEOUT`: `start.sh` で Gunicorn 起動時に参照（省略可）。

## ロギング
- `src/infrastructure/logger.py` の `StdLogger` を使用。
- Gunicorn の root ハンドラを尊重しつつ、名前付きロガー側は DEBUG レベルに設定。
- 主要ロガー
  - `src.app`: 起動時ログ、通知結果など
  - `src.infrastructure.*`: アダプタの入出力など

## テスト
- ランナー
```bash
PYTHONPATH=. pytest
```
- 種別
  - ユニットテスト（ロガー、Flex 生成 等）
  - E2E（メッセージハンドラ直接呼び出し）
- 注意
  - PEP 420 名前空間パッケージ。`PYTHONPATH=.` が必要。

## デプロイ/起動
- `Procfile` → `start.sh` → Gunicorn（`src.app:app`）
- `render.yaml` の `PORT` は 8080 を想定（環境に合わせて上書き可）。
- ローカル開発で `flask run` は使用しない（Gunicorn 前提）。

## セキュリティ
- `LINE_CHANNEL_SECRET` と `LINE_CHANNEL_ACCESS_TOKEN` は機密。
- Webhook 署名検証失敗時は 400 を返し、処理を中断。
- OpenAI API キーはログに出力しない。エラーメッセージは一般化。

## 既知の制約・メモ
- PokeAPI 取得は簡易実装。ネットワーク障害時は英名や不完全情報となる可能性。
- Gunicorn ワーカー数が複数の場合でも、/tmp フラグで起動通知は 1 回に抑制される設計。
- OpenAI API のタイムアウトは 30 秒に設定。
- OpenAI API のレスポンス処理は Chat Completions API の標準形式（`choices[0].message.content`）のみ対応。

## 参照
- LINE Messaging API: https://developers.line.biz/ja/reference/messaging-api/
- OpenAI API: https://platform.openai.com/docs/api-reference/chat
- PokeAPI: https://pokeapi.co/
