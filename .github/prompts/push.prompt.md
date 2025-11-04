---
mode: agent
---

以下の指示に従って、GitHubリポジトリのプッシュ操作を行ってください。

1. テストを実行してください。
  - PYTHONPATH=. pytest
1. 変更をステージングエリアに追加してください。
  - git add .
1. 変更内容を確認し、適切なコミットメッセージを作成してください。
  - git commit -m "Fix test cases to use postback_data"
1. 変更をリモートリポジトリにプッシュしてください。
  - git push origin main