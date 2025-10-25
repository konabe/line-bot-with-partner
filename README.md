# LINE Bot (Python) minimal template

Flask + line-bot-sdk を使った最小の echo Bot テンプレートです。
## Developer notes: src/ layout

This repository now uses a `src/` layout: the actual application code lives under the `src/` package (for example `src/app.py`, `src/umigame.py`, `src/openai_helpers.py`, etc.).

To run tests locally (recommended):

```bash
# from repository root
PYTHONPATH=$(pwd) pytest -q
```

Or alternatively install the package in editable mode if you add a packaging manifest (not provided by default):

```bash
python -m pip install -e .
pytest -q
```

Top-level shim modules were removed; tests and CI were adjusted to import from `src.*` directly. CI already sets `PYTHONPATH` before running tests.
## Notes about removing top-level shim modules

We removed several top-level shim files (for example `src/umigame.py`) to prefer direct imports from the new DDD layout (`src.domain.*`, `src.application.*`, `src.infrastructure.*`). If you remove a tracked shim file in future, follow these steps to avoid inconsistencies:

- Use `git rm` to remove tracked files so the index is updated correctly:

```bash
git rm src/umigame.py
git commit -m "Remove shim"
git push origin <branch>
```

- Verify there are no remaining tracked shim files:

```bash
git ls-files 'src/*' | grep -E "(^src/umigame.py|^src/messaging.py|^src/openai_helpers.py)" || true
```

- Run tests the same way CI does:

```bash
PYTHONPATH=. pytest -q
```

If you'd like, I can add an automated CI check (`scripts/check-no-shims.sh`) or a `pre-commit` hook to enforce this policy.
## 起動通知機能 (Startup Notify)

サーバー起動時に LINE (push) で起動完了メッセージを受け取りたい場合、以下の環境変数を設定します。
# LINE Bot (Python) minimal template

Flask + line-bot-sdk を使った最小の echo Bot テンプレートです。

準備:

1. `.env.example` をコピーして環境変数を設定してください。
2. 依存をインストール: `pip install -r requirements.txt`
3. ローカルで実行: `python app.py`

Webhook を動かすには public URL が必要です（ngrok 等を使用）。

## 起動通知機能 (Startup Notify)

サーバー起動時に LINE (push) で起動完了メッセージを受け取りたい場合、以下の環境変数を設定します。

| 環境変数 | 必須 | 説明 |
|----------|------|------|
| `STARTUP_NOTIFY_ENABLED` | 任意 | `1` で有効化 (未設定/その他は無効) |
| `STARTUP_NOTIFY_USER_ID` | 有効化時必須 | push 先のユーザー ID (Bot の友だちである必要があります) |
| `STARTUP_NOTIFY_MESSAGE` | 任意 | 送信する文面。省略時: `サーバーが起動しました ✅` |

例 (.env):

```
STARTUP_NOTIFY_ENABLED=1
STARTUP_NOTIFY_USER_ID=Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
STARTUP_NOTIFY_MESSAGE=Bot サーバーが再起動しました (deploy)
```

Render などの PaaS での再デプロイ時にもプロセス起動直後に 1 回だけ送信されます。複数ワーカーを立てる構成ではワーカー毎に送信される可能性があるため注意してください (必要なら外部ストレージ/DBで排他制御してください)。

## 任意の場所の天気を取得

LINE で「◯◯の天気」と送ると、OpenWeatherMap APIを使用して現在の天気を返信します。

例:

```
東京の天気
大阪の天気
博多の天気
```

### 必要な環境変数

| 環境変数 | 必須 | 説明 |
|----------|------|------|
| `OPENWEATHERMAP_API_KEY` | 必須 | OpenWeatherMap APIキー |

OpenWeatherMap APIキーの取得方法:
1. [OpenWeatherMap](https://openweathermap.org/api)でアカウント作成
2. API Keysページで無料のAPIキーを取得
3. `.env`ファイルに`OPENWEATHERMAP_API_KEY=your_api_key_here`を追加

対応都市: 東京、大阪、名古屋、福岡、博多、札幌、仙台、広島、京都、神戸、横浜

解決に失敗した場合は「◯◯の天気情報の取得に失敗しました」と返答します。
# What is this?

The github.dev web-based editor is a lightweight editing experience that runs entirely in your browser. You can navigate files and source code repositories from GitHub, and make and commit code changes.

There are two ways to go directly to a VS Code environment in your browser and start coding:

* Press the . key on any repository or pull request.
* Swap `.com` with `.dev` in the URL. For example, this repo https://github.com/github/dev becomes http://github.dev/github/dev

Preview the gif below to get a quick demo of github.dev in action.

![github dev](https://user-images.githubusercontent.com/856858/130119109-4769f2d7-9027-4bc4-a38c-10f297499e8f.gif)

# Why?
It’s a quick way to edit and navigate code. It's especially useful if you want to edit multiple files at a time or take advantage of all the powerful code editing features of Visual Studio Code when making a quick change. For more information, see our [documentation](https://github.co/codespaces-editor-help).
