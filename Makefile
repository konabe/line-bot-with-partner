.PHONY: help setup test test-verbose clean install-deps format lint

help:  ## このヘルプメッセージを表示
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## 開発環境のセットアップ
	@echo "🚀 開発環境をセットアップ中..."
	./scripts/setup-dev-env.sh

setup-dev:  ## 開発用セットアップ（仮想環境作成・依存インストール・pre-commit導入）
	@echo "🚀 開発環境（venv）をセットアップ中..."
	./scripts/setup-dev-env.sh

install-deps:  ## 依存関係のインストール
	@echo "📦 依存関係をインストール中..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:  ## テストの実行
	@echo "🧪 テストを実行中..."
	PYTHONPATH=. pytest -q

test-verbose:  ## テストの実行 (詳細表示)
	@echo "🧪 テストを実行中 (詳細表示)..."
	PYTHONPATH=. pytest -v

test-coverage:  ## カバレッジ付きテストの実行
	@echo "🧪 カバレッジ付きテストを実行中..."
	PYTHONPATH=. pytest --cov=src --cov-report=term-missing tests/

test-coverage-html:  ## カバレッジ付きテストの実行（HTMLレポート生成）
	@echo "🧪 カバレッジ付きテストを実行中（HTMLレポート生成）..."
	PYTHONPATH=. pytest --cov=src --cov-report=html --cov-report=term-missing tests/
	@echo "📊 HTMLレポートが htmlcov/index.html に生成されました"

format:  ## コードフォーマット
	@echo "✨ コードをフォーマット中..."
	black src/ tests/

lint:  ## 静的解析の実行
	@echo "🔍 静的解析を実行中..."
	flake8 src/ tests/

clean:  ## キャッシュファイルの削除
	@echo "🧹 キャッシュファイルを削除中..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".coverage" -delete
	find . -name "coverage.xml" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .pytest_cache/

check:  ## 全チェックの実行（テスト、lint、フォーマット確認）
	@echo "📋 全チェックを実行中..."
	@echo "1. フォーマットチェック..."
	black --check src/ tests/
	@echo "2. 静的解析..."
	flake8 src/ tests/
	@echo "3. テスト実行..."
	PYTHONPATH=. pytest -q
	@echo "✅ 全てのチェックが完了しました！"

run:  ## アプリケーションの起動
	@echo "🚀 アプリケーションを起動中..."
	PYTHONPATH=. python src/app.py
