.PHONY: test generate run-all benchmark reports frontend-build frontend-test api frontend docker-config

test:
	cd backend && python -m pytest

generate:
	python scripts/generate_world.py --seed 42 --accounts 10000 --transactions 100000

run-all:
	python scripts/run_all_experiments.py

benchmark:
	python scripts/benchmark_experiments.py

reports:
	python scripts/export_demo_reports.py

api:
	cd backend && python -m fraudwar.cli serve

frontend:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm run test:e2e

docker-config:
	docker compose config
