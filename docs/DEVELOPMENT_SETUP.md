# 開発環境セットアップガイド

このプロジェクトでは、新しい開発者が迅速かつ確実に開発環境をセットアップできるよう、自動化ツールとガイドラインを提供しています。

## 🚀 クイックスタート

### 1. 依存関係とツールのインストール

```bash
# 自動セットアップスクリプトを実行
./scripts/setup-dev-env.sh

# または Make を使用
make setup
```

### 2. 開発タスクの実行

```bash
# テスト実行
make test

# 詳細なテスト実行
make test-verbose

# コードフォーマット
make format

# 静的解析（lint）
make lint

# すべてのチェックを実行
make check
```

## 📝 開発フロー

1. **環境セットアップ**: `make setup` で依存関係をインストール
2. **コード作成**: 新しい機能やバグ修正を実装
3. **フォーマット**: `make format` でコードを自動整形
4. **テスト**: `make test` でユニットテストを実行
5. **チェック**: `make lint` で静的解析を実行
6. **コミット**: 問題がなければ変更をコミット

## 🛠️ ツール構成

- **pytest**: テストフレームワーク（バージョン 8.4.0 以上）
- **black**: コードフォーマッター（行長120文字）
- **flake8**: 静的解析ツール
- **pytest-cov**: カバレッジ測定

## 🔧 VS Code 設定

VS Code を使用している場合、自動的に以下が設定されます：

- Python インタープリター: `/usr/local/python/3.12.1/bin/python`
- テスト自動検出: pytest
- フォーマッター: black
- リンター: flake8

## ⚠️ トラブルシューティング

### pytest のインポートエラー

```bash
# Python 環境と pytest の確認
python --version
pytest --version

# セットアップスクリプトを再実行
./scripts/setup-dev-env.sh
```

### VS Code での型チェックエラー

1. VS Code のコマンドパレット（Ctrl+Shift+P）を開く
2. "Python: Select Interpreter" を選択
3. `/usr/local/python/3.12.1/bin/python` を選択

### 依存関係の問題

```bash
# requirements-dev.txt の再インストール
pip install -r requirements-dev.txt

# 仮想環境のリセット（必要に応じて）
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

## 📋 チェックリスト

新しいチーム メンバーが開発を開始する前に確認すべき事項：

- [ ] `make setup` が正常に実行される
- [ ] `make test` ですべてのテストがパスする
- [ ] `make lint` でエラーが出ない  
- [ ] VS Code で型チェックエラーが表示されない
- [ ] `.env` ファイルが設定されている（必要に応じて）

## 🎯 継続的改善

このセットアップスクリプトと設定は、チームの開発効率を向上させるために継続的に改善されます。問題や改善提案があれば、イシューやプルリクエストでお知らせください。