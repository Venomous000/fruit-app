# Lifecycle

up:                ## Start all containers (build if needed)
	docker-compose up --build -d

down:              ## Stop all containers (keep data)
	docker-compose down

nuke:              ## Stop all containers AND delete database volume
	docker-compose down -v

restart:           ## Restart everything fresh
	docker-compose down
	docker-compose up --build -d

logs:              ## Follow logs from all containers
	docker-compose logs -f

logs-back:         ## Follow backend logs only
	docker-compose logs -f backend

logs-front:        ## Follow frontend logs only
	docker-compose logs -f frontend

#  Database 

seed:              ## Seed the database with fruits from fruitList.json
	docker-compose exec backend python -m app.scripts.seed_db

db-shell:          ## Open a psql shell inside the database container
	docker-compose exec db psql -U postgres -d fruitdb

#  Testing 

test:              ## Run all backend tests
	pytest

test-cov:          ## Run tests with coverage report
	pytest -v --cov=app --cov-report=term-missing

#  Utilities 

ps:                ## Show running containers and their status
	docker-compose ps

shell-back:        ## Open a bash shell in the backend container
	docker-compose exec backend bash

shell-front:       ## Open a bash shell in the frontend container
	docker-compose exec frontend bash
