# LINE Bot with Partner 仕様書

最終更新: 2025-10-26

## 概要
- 本アプリケーションは LINE Messaging API を利用したチャットボットです。
- コマンド検出により、以下の機能を提供します。
  - 「ウミガメのスープ」出題・Q&A
  - 「じゃんけん」テンプレート送信
  - 「天気」クエリ解析（例: 「東京の天気」）
  - 「今日のご飯」ChatGPT からの提案
  - 「ポケモン」ランダム図鑑（Flex Message）
  - その他テキストは ChatGPT による応答
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
  - `src/application/routes.py`: `/health`, `/callback` エンドポイント
  - `src/application/message_handlers.py`: テキストメッセージのコマンド判定と処理
  - `src/application/handler_registration.py`: ハンドラの DI 構成
  - `src/application/startup_notify.py`: 起動通知ヘルパ
  - `src/infrastructure/line_adapter.py`: LINE Messaging API アダプタ
  - `src/infrastructure/line_model/zukan_flex.py`: ポケモン図鑑の Flex バブル生成
  - `src/infrastructure/openai_helpers.py`: OpenAI クライアント（`OpenAIClient`）
  - `src/infrastructure/logger.py`: DI 可能なロガー

## 外部サービス・依存
- LINE Messaging API v3
  - Webhook 署名検証
  - Reply/Push メッセージ送信
  - Flex Message（type:flex, altText 必須, contents=bubble など）
- OpenAI API（Chat Completions）
  - yes/no 回答、ウミガメ出題生成、通常応答、食事提案
- PokeAPI（`_get_random_pokemon_zukan_info`）
  - ランダムなポケモン情報取得
- 天気情報
  - `infrastructure/weather_adapter.py`（実装に依存）

## エンドポイント
- `GET /health`
  - 健康チェック。200/OK を返す。
- `POST /callback`
  - LINE Webhook 受信。
  - 署名検証失敗: 400。
  - ハンドラ内エラー: ログ出力＋可能な限り安全に返信。

## メッセージ処理（コマンドと挙動）
`src/application/message_handlers.py` の `MessageHandler.handle_message` が判定。
- ウミガメのスープ
  - 「ウミガメのスープ」: モード開始。出題を返信。
  - 「ウミガメのスープ終了」: モード終了。
  - モード中: クローズドクエスチョンのみ受付（はい/いいえ判定）。
- 「直接送信テスト」
  - ユーザーへ push を試み、結果を返信（注: 実装上 `safe_reply_message` 使用）。
- 天気: テキストに「天気」を含む
  - 「◯◯の天気」から地名抽出。なければ東京で応答。
- じゃんけん: 完全一致「じゃんけん」
  - ボタンテンプレートを返信。
- 今日のご飯: 完全一致「今日のご飯」
  - ChatGPT の提案を返信（失敗時は案内メッセージ）。
- ポケモン: 完全一致「ポケモン」
  - ランダムなポケモンの図鑑を Flex で返信。
- それ以外
  - ChatGPT による通常応答。

## Flex Message（ポケモン図鑑）
- 送信オブジェクト例（SDK オブジェクトではなく dict を使用）:
```json
{
  "type": "flex",
  "altText": "ポケモン図鑑",
  "contents": { /* bubble オブジェクト */ }
}
```
- `contents` は `create_pokemon_zukan_flex_dict(info)` が返す bubble 互換 dict。
- altText は必須。空不可。

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
  - `OPENAI_MODEL`: 省略可（デフォルト `gpt-3.5-turbo`）。
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
- 「直接送信テスト」ハンドラは `safe_reply_message` を用いて push リクエストを送っており、実運用では `safe_push_message` へ切替が望ましい。
- PokeAPI 取得は簡易実装。ネットワーク障害時は英名や不完全情報となる可能性。
- Gunicorn ワーカー数が複数の場合でも、/tmp フラグで起動通知は 1 回に抑制される設計。

## 参照
- LINE Messaging API: https://developers.line.biz/ja/reference/messaging-api/
- OpenAI API: https://platform.openai.com/docs/api-reference/chat
- PokeAPI: https://pokeapi.co/
