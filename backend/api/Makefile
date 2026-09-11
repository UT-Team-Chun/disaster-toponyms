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

.PHONY: vis_coverage
vis_coverage:
	uv run coverage run -m pytest
	uv run coverage report
	uv run coverage html
	open htmlcov/index.html

.PHONY: gen-deps
gen-deps:
	uv run tach show --mermaid -o ../../docs/dependencies.mmd

.PHONY: dev
dev:
	uv run uvicorn src.app:app --reload --reload-dir src --reload-dir ../packages/alg --reload-dir ../packages/gateways

.PHONY: openapi-generate
openapi-generate:
	uv run python dev/generate_openapi.py > openapi.yaml


# Migration commands
migration-generate:
	docker compose exec api alembic revision --autogenerate -m "$(message)"

migration-upgrade:
	docker compose exec api alembic upgrade head

migration-upgrade-one:
	docker compose exec api alembic upgrade +1

migration-downgrade:
	docker compose exec api alembic downgrade -1

migration-clean:
	docker compose exec rdb psql -U rdb_user -d rdb_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	docker compose exec test-rdb psql -U test_user -d test_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"


# Docker commands
docker-build:
	docker image build -t api .

docker-run:
	docker container run -it --rm -p 8000:8000 api
