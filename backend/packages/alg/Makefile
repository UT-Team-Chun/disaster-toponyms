.PHONY: fmt
fmt:
	uv run ruff format .
	uv run ruff check .

.PHONY: fix
fix:
	uv run ruff format .
	uv run ruff check . --fix

.PHONY: lint
lint:
	uv run ruff check .
	uv run tach check
	uv run mypy .

.PHONY: test
test:
	uv run pytest . -vv

.PHONY: coverage
coverage:
	uv run coverage run -m pytest
	uv run coverage report

# ===========================
# 警鐘地名データセット
# ===========================

# 公開データを data/raw/ に取得する。
# pdftotext (poppler) が必要: brew install poppler
.PHONY: download-data
download-data:
	@command -v pdftotext >/dev/null || { \
		echo "pdftotext が見つかりません。brew install poppler を実行してください。"; \
		exit 1; \
	}
	@uv run python scripts/download_sources.py

# データセットをビルドし、frontend/public/data に静的ファイルを書き出す
.PHONY: build-data
build-data:
	@uv run python scripts/build_toponym_dataset.py

# ネットワークとLLMを使わず、キャッシュのみで再現ビルドする
.PHONY: build-data-offline
build-data-offline:
	@uv run python scripts/build_toponym_dataset.py --offline
