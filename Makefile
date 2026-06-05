.PHONY: bootstrap verify test context-check db-up db-down db-migrate db-smoke api api-postgres demo

bootstrap:
	./scripts/bootstrap.sh

verify:
	./scripts/verify.sh

test:
	cd backend && PYTHONPATH=. python -m pytest -q

context-check:
	./scripts/validate_workspace.sh

db-up:
	docker compose up -d db

db-down:
	docker compose down

db-migrate:
	./scripts/db_apply_migrations.sh

db-smoke:
	python scripts/db_smoke_check.py

api:
	./scripts/run_api.sh --memory

api-postgres:
	./scripts/run_api.sh --postgres

demo:
	python scripts/demo_mvp.py
