install:
	uv sync

install-dev:
	uv sync --group dev

format:
	uv run isort ghsearch/ tests/
	uv run black ghsearch/ tests/

black:
	uv run black --check ghsearch/ tests/

flake:
	uv run flake8 ghsearch/ tests/

typing:
	uv run mypy -p ghsearch

lint: black flake typing

unit:
	uv run pytest -sv tests/unit

coverage-run:
	uv run coverage run --source=ghsearch/ --omit ghsearch/cli.py --branch -m pytest tests/unit --junitxml=build/test.xml -v

coverage: coverage-run
	uv run coverage xml -i -o build/coverage.xml
	uv run coverage report

coverage-html: coverage-run
	uv run coverage html && open htmlcov/index.html

test: lint unit

.PHONY: install install-dev format black flake typing lint unit coverage-run coverage coverage-html test
