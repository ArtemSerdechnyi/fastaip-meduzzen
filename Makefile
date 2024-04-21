DC = docker-compose
COMPOSE = docker-compose.yaml
COMPOSE_DEV = docker-compose-dev.yaml
APP_PATH = app/main.py

.PHONY: runapp
runapp:
	PYTHONPATH=$(shell pwd) poetry run python ${APP_PATH}

.PHONY: rundev
rundev:
	${DC} --env-file .env.docker -f ${COMPOSE_DEV}  up --build

.PHONY: runall
runall:
	${DC} --env-file .env.docker -f ${COMPOSE}  up --build

.PHONY: drop
drop:
	${DC} down && doker network prune --force

.PHONY: expre
expre:
	poetry export --without-hashes --format=requirements.txt > requirements.txt

.PHONY: tests
tests:
	poetry run pytest -s tests/ -W ignore::DeprecationWarning

.PHONY: mm
mm:
	poetry run alembic revision --autogenerate

.PHONY: migrate
migrate:
	poetry run alembic upgrade heads
