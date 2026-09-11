# Backend Makefile - Run commands across api, alg, and gateways

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make fmt            - Format code on all packages (api, alg, gateways)"
	@echo "  make fix            - Run auto-fix on all packages (api, alg, gateways)"
	@echo "  make lint           - Run linting on all packages (api, alg, gateways)"
	@echo "  make test           - Run tests on all packages (api, alg, gateways)"
	@echo ""
	@echo "CI check targets:"
	@echo "  make check-format   - Check if code is formatted (used in CI)"
	@echo "  make check-deps     - Check if dependency diagram is up to date (used in CI)"
	@echo "  make check-openapi  - Check if OpenAPI spec is up to date (used in CI)"
	@echo "  make ci             - Run all CI checks"
	@echo ""
	@echo "API-specific targets:"
	@echo "  make dev            - Start development server (api only)"
	@echo "  make coverage       - Run coverage report (api only)"
	@echo "  make vis_coverage   - Visualize coverage (api only)"
	@echo "  make gen-deps       - Generate dependency diagram (api only)"
	@echo "  make gen            - Generate OpenAPI specification (api only)"
	@echo ""
	@echo "Disaster toponym dataset targets:"
	@echo "  make download-data  - Download the public source datasets into data/raw/"
	@echo "  make build-data     - Build the dataset into frontend/public/data/"
	@echo "  make build-data-offline - Rebuild from caches only (no network, no LLM)"

.PHONY: fmt
fmt:
	@echo "==> Running fmt on api..."
	@cd api && $(MAKE) fmt
	@echo ""
	@echo "==> Running fmt on packages/alg..."
	@cd packages/alg && $(MAKE) fmt
	@echo ""
	@echo "==> Running fmt on packages/gateways..."
	@cd packages/gateways && $(MAKE) fmt
	@echo ""
	@echo "✅ All formatting completed!"

.PHONY: fix
fix:
	@echo "==> Running fix on api..."
	@cd api && $(MAKE) fix
	@echo ""
	@echo "==> Running fix on packages/alg..."
	@cd packages/alg && $(MAKE) fix
	@echo ""
	@echo "==> Running fix on packages/gateways..."
	@cd packages/gateways && $(MAKE) fix
	@echo ""
	@echo "✅ All auto-fixes completed!"

.PHONY: lint
lint:
	@echo "==> Running lint on api..."
	@cd api && $(MAKE) lint
	@echo ""
	@echo "==> Running lint on packages/alg..."
	@cd packages/alg && $(MAKE) lint
	@echo ""
	@echo "==> Running lint on packages/gateways..."
	@cd packages/gateways && $(MAKE) lint
	@echo ""
	@echo "✅ All lint checks passed!"

.PHONY: test
test:
	@echo "==> Running tests on api..."
	@cd api && $(MAKE) test
	@echo ""
	@echo "==> Running tests on packages/alg..."
	@cd packages/alg && $(MAKE) test
	@echo ""
	@echo "==> Running tests on packages/gateways..."
	@cd packages/gateways && $(MAKE) test
	@echo ""
	@echo "✅ All tests passed!"

.PHONY: license
license:
	@uv run python scripts/generate_licenses.py

# ===========================
# 警鐘地名データセット (packages/alg)
# ===========================

.PHONY: download-data
download-data:
	@cd packages/alg && $(MAKE) download-data

.PHONY: build-data
build-data:
	@cd packages/alg && $(MAKE) build-data

.PHONY: build-data-offline
build-data-offline:
	@cd packages/alg && $(MAKE) build-data-offline

# ===========================
# API-specific targets
# ===========================

.PHONY: dev
dev:
	@cd api && $(MAKE) dev

.PHONY: coverage
coverage:
	@cd api && $(MAKE) coverage

.PHONY: vis_coverage
vis_coverage:
	@cd api && $(MAKE) vis_coverage

.PHONY: gen-deps
gen-deps:
	@cd api && $(MAKE) gen-deps

.PHONY: gen
gen:
	@cd api && $(MAKE) openapi-generate

# ===========================
# CI check targets
# ===========================

.PHONY: check-format
check-format:
	@echo "==> Checking code formatting..."
	@$(MAKE) fmt
	@if ! git diff --quiet; then \
		echo ""; \
		echo "❌ Code is not formatted. Please run 'make fmt' locally."; \
		echo ""; \
		git diff --stat; \
		exit 1; \
	fi
	@echo "✅ Code formatting is up to date!"

.PHONY: check-deps
check-deps:
	@echo "==> Checking dependency diagram..."
	@cd api && $(MAKE) gen-deps
	@if ! git diff --quiet -- ../docs/dependencies.mmd; then \
		echo ""; \
		echo "❌ Dependency diagram is out of date. Please run 'make gen-deps' locally."; \
		echo ""; \
		git diff -- ../docs/dependencies.mmd; \
		exit 1; \
	fi
	@echo "✅ Dependency diagram is up to date!"

.PHONY: check-openapi
check-openapi:
	@echo "==> Checking OpenAPI specification..."
	@cd api && $(MAKE) openapi-generate
	@if ! git diff --quiet -- api/openapi.yaml; then \
		echo ""; \
		echo "❌ OpenAPI specification is out of date. Please run 'make openapi-generate' locally."; \
		echo ""; \
		git diff -- api/openapi.yaml; \
		exit 1; \
	fi
	@echo "✅ OpenAPI specification is up to date!"

.PHONY: ci
ci: check-format lint test check-deps check-openapi
	@echo ""
	@echo "✅ All CI checks passed!"
