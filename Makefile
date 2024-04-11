
.PHONY: run
run:
	PYTHONPATH=$(shell pwd) poetry run python app/main.py

.PHONY: expre
expre:
	poetry export --without-hashes --format=requirements.txt > requirements.txt

.PHONY: tests
tests:
	poetry run pytest tests/
