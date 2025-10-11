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

LINE で「◯◯の天気」と送ると、◯◯ を地名としてジオコーディングし現在の天気を返信します。

例:

```
東京の天気
大阪の天気です
札幌の天気？
```

解決に失敗した場合は「『◯◯』の天気を見つけられませんでした」と返答します。内部では Open-Meteo Geocoding API と Forecast API を利用しています。頻度が高い場合はレート制限に注意してください。

## 絵文字じゃんけん機能

LINE で絵文字や日本語でじゃんけんができます。Bot がランダムに手を出して勝敗を判定します。

使い方:

* 絵文字で送信: `✊` (グー), `✋` (パー), `✌️` (チョキ)
* 日本語で送信: `グー`, `パー`, `チョキ` (ひらがなも可)

例:

```
ユーザー: ✊
Bot: あなた: ✊ グー
     Bot: ✌️ チョキ
     
     あなたの勝ち！
```

勝敗の判定:
* あいこ: 同じ手
* あなたの勝ち: グー > チョキ, パー > グー, チョキ > パー
* あなたの負け: その他

# What is this?

The github.dev web-based editor is a lightweight editing experience that runs entirely in your browser. You can navigate files and source code repositories from GitHub, and make and commit code changes.

There are two ways to go directly to a VS Code environment in your browser and start coding:

* Press the . key on any repository or pull request.
* Swap `.com` with `.dev` in the URL. For example, this repo https://github.com/github/dev becomes http://github.dev/github/dev

Preview the gif below to get a quick demo of github.dev in action.

![github dev](https://user-images.githubusercontent.com/856858/130119109-4769f2d7-9027-4bc4-a38c-10f297499e8f.gif)

# Why?
It’s a quick way to edit and navigate code. It's especially useful if you want to edit multiple files at a time or take advantage of all the powerful code editing features of Visual Studio Code when making a quick change. For more information, see our [documentation](https://github.co/codespaces-editor-help).
