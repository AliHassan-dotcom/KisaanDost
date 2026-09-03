.PHONY: up down logs ps migrate revision test-backend lint-backend analyze-mobile test-mobile

up:            ## build & start db, redis, api, worker, beat
	docker compose up -d --build

down:          ## stop everything
	docker compose down

ps:
	docker compose ps

logs:          ## tail api/worker/beat logs
	docker compose logs -f api worker beat

migrate:       ## apply alembic migrations
	docker compose exec api alembic upgrade head

revision:      ## create migration: make revision m="add farms table"
	docker compose exec api alembic revision --autogenerate -m "$(m)"

test-backend:
	cd backend && pytest

lint-backend:
	cd backend && ruff check app && mypy app

analyze-mobile:
	cd mobile && flutter analyze

test-mobile:
	cd mobile && flutter test
