install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

format:
	isort -l 120 --profile black ghsearch/ tests/
	black -l 120 -t py37 ghsearch/ tests/ *.py

black:
	black -l 120 -t py37 --check ghsearch/ tests/ *.py

flake:
	flake8 ghsearch/ tests/

typing:
	mypy -p ghsearch

lint: black flake typing

unit:
	pytest -sv tests/unit

coverage-run:
	coverage run --source=ghsearch/ --omit ghsearch/cli.py --branch -m pytest tests/unit --junitxml=build/test.xml -v

coverage: coverage-run
	coverage xml -i -o build/coverage.xml
	coverage report

coverage-html: coverage-run
	coverage html && open htmlcov/index.html

test: lint unit

.PHONY: install install-dev format black flake typing lint unit coverage-run coverage coverage-html test
