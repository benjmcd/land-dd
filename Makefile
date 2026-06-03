.PHONY: bootstrap verify test context-check db-up db-down db-migrate db-smoke

bootstrap:
	./scripts/bootstrap.sh

verify:
	./scripts/verify.sh

test:
	cd backend && PYTHONPATH=. python -m pytest -q

context-check:
	./scripts/agent-context-check.sh

db-up:
	docker compose up -d db

db-down:
	docker compose down

db-migrate:
	./scripts/db_apply_migrations.sh

db-smoke:
	python scripts/db_smoke_check.py
