install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

format:
	isort -l 120 --profile black ghsearch/ tests/
	black -l 120 -t py37 ghsearch/ tests/

black:
	black -l 120 -t py37 --check ghsearch/ tests/

flake:
	flake8 ghsearch/ tests/

typing:
	mypy -p ghsearch

lint: black flake typing

unit:
	pytest -sv tests/unit

coverage:
	coverage run --source=ghsearch/ --branch -m pytest tests/unit --junitxml=build/test.xml -v
	coverage xml -i -o build/coverage.xml
	coverage report

test: lint unit

.PHONY: install install-dev format black flake typing lint unit coverage test
