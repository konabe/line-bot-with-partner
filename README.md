# LINE Bot with Partner

Flask + line-bot-sdk を使った LINE Bot アプリケーションです。

## 機能

- **天気情報**: 「◯◯の天気」で指定地域の天気を取得
- **じゃんけん**: 「じゃんけん」でじゃんけんゲーム
- **今日のご飯**: 「今日のご飯」で ChatGPT による料理提案
- **ポケモン図鑑**: 「ポケモン」でランダムなポケモン情報を表示
- **ぐんまちゃんとの会話**: 「ぐんまちゃん、」で始まるメッセージに ChatGPT が応答

## セットアップ

### 🚀 クイックスタート（新規メンバー向け）

開発環境の自動セットアップを実行：
```bash
# 自動セットアップスクリプト（推奨）
./scripts/setup-dev-env.sh

# または Make を使用
make setup
```

### 手動セットアップ

1. 依存パッケージのインストール:
```bash
# 本番依存関係
pip install -r requirements.txt

# 開発依存関係（テスト、リント等）
pip install -r requirements-dev.txt
```

2. 環境変数の設定（`.env.example` を参考に `.env` を作成）:
```bash
# LINE
LINE_CHANNEL_SECRET=your_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini  # 省略可（デフォルト: gpt-5-mini）

# OpenWeatherMap
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key

# 起動通知（任意）
ADMIN_USER_ID=Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_STARTUP_MESSAGE=サーバーが起動しました。
```

3. ローカル実行（開発時）:
```bash
# Gunicornで起動（推奨）
./start.sh

# または直接
gunicorn src.app:app --bind 0.0.0.0:8080
```

Webhook を動かすには public URL が必要です（ngrok 等を使用）。

## 開発者向け情報

## Developer setup (recommended)

To make development easier and keep code style consistent, run the following once after cloning:

```bash
# create a virtual env, activate it, then:
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

# install pre-commit git hooks for this repository
python -m pre_commit install
# optionally install pre-push hooks as well
python -m pre_commit install --hook-type pre-push
```

After this, `pre-commit` will run configured checks (isort, black, flake8, etc.) automatically on commit.

If you want to run all hooks manually anytime:

```bash
python -m pre_commit run --all-files
```


### 🛠️ 開発環境

#### VS Code 設定
本プロジェクトには以下の VS Code 設定が含まれています：

- **Python 環境**: 自動検出とPYTHONPATH設定
- **テスト**: pytest 統合とテストディスカバリ
- **リント**: 基本的な型チェック（Pylance）
- **推奨拡張**: Python、Copilot等の開発支援ツール

#### 使用可能なコマンド
```bash
# テスト実行
make test                # 簡潔な出力
make test-verbose       # 詳細な出力
PYTHONPATH=. pytest -q # 直接実行

# コード品質
make format             # コードフォーマット (Black)
make lint              # 静的解析 (flake8)

# 環境管理
make clean             # キャッシュファイル削除
make install-deps      # 依存関係再インストール

# アプリ起動
make run               # 開発サーバー起動
./start.sh            # 本番サーバー起動
```

#### トラブルシューティング

**pytest インポートエラーが発生する場合：**
```bash
# Python 環境に pytest がインストールされているか確認
python -c "import pytest; print(pytest.__version__)"

# インストールされていない場合
pip install pytest

# または開発依存関係を再インストール
pip install -r requirements-dev.txt
```

**VS Code で型チェックエラーが表示される場合：**
1. VS Code で `Ctrl+Shift+P` → "Python: Select Interpreter"
2. 適切な Python 環境を選択
3. `F1` → "Developer: Reload Window" で設定リロード

### プロジェクト構成

このリポジトリは `src/` レイアウトを使用しています:

```
src/
├── app.py                    # Flask アプリのエントリポイント
├── application/              # アプリケーション層
│   ├── routes.py            # エンドポイント定義
│   ├── message_handlers.py  # メッセージハンドラ
│   ├── postback_handlers.py # ポストバックハンドラ
│   └── usecases/            # ユースケース層
├── domain/                   # ドメイン層
│   ├── models/              # ドメインモデル
│   └── services/            # ドメインサービス
├── infrastructure/           # インフラ層
│   ├── adapters/            # 各種アダプタ実装（移動済み）
│   │   ├── line_adapter.py
│   │   ├── openai_adapter.py
│   │   └── weather_adapter.py
│   ├── line_model/          # LINE 用テンプレート等
│   └── logger.py            # ロガー実装
└── ports/                    # ポート定義
```

### 設計メモ: ポストバックルーティングの責務分離

このリポジトリではメッセージイベントとポストバックイベントのルーティング責務を分離しています。

- `src/application/message_router.py` はテキストメッセージのルーティングに専念します。
- ポストバックイベント（例: ボタンの押下で送られる `postback.data`）は `src/application/postback_router.py` の `PostbackRouter` が扱います。

handler の登録は `src/application/handler_registration.py` で行われており、MessageEvent は `MessageRouter`、PostbackEvent は `PostbackRouter` に振り分けられます。

今回の設計変更により、ポストバック処理の拡張やテストがより容易になります。外部から直接 `MessageRouter.route_postback` を呼んでいるコードがある場合は、`PostbackRouter.route_postback` に差し替えてください。

短い移行手順:

1. `MessageRouter.route_postback(...)` を使っている箇所を検索します。
2. `PostbackRouter` を初期化して `route_postback(...)` を呼ぶように置換します。
3. 既存のユニットテストは `tests/application/test_postback_handlers.py` を参考に更新してください。

例:

```py
# 旧: message_router_instance.route_postback(event)
# 新:
postback_router = PostbackRouter(line_adapter, logger=logger, janken_service=service)
postback_router.route_postback(event)
```


### テスト実行

```bash
# リポジトリルートから実行
PYTHONPATH=. pytest

# または詳細表示
PYTHONPATH=. pytest -v
```

PEP 420 の名前空間パッケージを使用しているため、`PYTHONPATH=.` の設定が必要です。

## アダプタ移動について（注記）

アダプタ実装は `src/infrastructure/adapters/` に移動しました。リポジトリ内の呼び出し元は新しいパスへ更新済みで、
トップレベルにあった互換性用の shim は削除されています。今後は新しいパスで直接インポートしてください。


### コーディングルール

- ドメイン駆動設計（DDD）に基づいた設計
- すべてのコード変更には対応するユニットテストを追加
- テストファイルは `tests/` ディレクトリ配下に `src/` と同じパス構成で配置
- コメントは日本語で記述
- global宣言は使用しない
- 不要になったコードは削除（互換性は考慮しない）

## 起動通知機能

サーバー起動時に LINE で起動完了メッセージを受け取りたい場合、以下の環境変数を設定します。

| 環境変数 | 必須 | 説明 |
|----------|------|------|
| `ADMIN_USER_ID` | 任意 | push 先のユーザー ID（Bot の友だちである必要があります） |
| `ADMIN_STARTUP_MESSAGE` | 任意 | 送信する文面。省略時: `サーバーが起動しました。` |

例:
```bash
ADMIN_USER_ID=Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_STARTUP_MESSAGE=Bot サーバーが再起動しました
```

Render などの PaaS での再デプロイ時にもプロセス起動直後に 1 回だけ送信されます。
複数ワーカーを立てる構成では `/tmp/line-bot-startup-notified` フラグで 1 回のみに制御されます。

## 天気情報機能

LINE で「◯◯の天気」と送ると、OpenWeatherMap API を使用して現在の天気を返信します。

例:
```
東京の天気
大阪の天気
博多の天気
```

対応都市: 東京、大阪、名古屋、福岡、博多、札幌、仙台、広島、京都、神戸、横浜

### OpenWeatherMap APIキーの取得方法

1. [OpenWeatherMap](https://openweathermap.org/api) でアカウント作成
2. API Keys ページで無料の API キーを取得
3. `.env` ファイルに `OPENWEATHERMAP_API_KEY=your_api_key_here` を追加

## 技術スタック

- **Python 3.12+**
- **Flask**: Web フレームワーク
- **Gunicorn**: WSGI サーバー
- **line-bot-sdk**: LINE Messaging API SDK
- **OpenAI API**: Chat Completions API（gpt-4o-mini / gpt-5-mini）
- **OpenWeatherMap API**: 天気情報取得
- **PokeAPI**: ポケモン情報取得

## デプロイ

Render などの PaaS では `render.yaml` を使用して自動デプロイできます。

必要な環境変数:
- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`
- `OPENAI_API_KEY`
- `OPENWEATHERMAP_API_KEY`
- `ADMIN_USER_ID`（任意）

## ライセンス

MIT

## 参考リンク

- [LINE Messaging API](https://developers.line.biz/ja/reference/messaging-api/)
- [OpenAI API](https://platform.openai.com/docs/api-reference/chat)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [PokeAPI](https://pokeapi.co/)
