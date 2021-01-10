import contextlib
from collections import defaultdict
from typing import Callable, List

import click
import github


def get_progress_message(result):
    if result is not None:
        return f"Checking result for {result.repository.full_name}"


class VerboseProgressPrinter(contextlib.AbstractContextManager):
    def __init__(self, results):
        self.iterator = iter(results)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def __iter__(self):
        return self

    def __next__(self):
        next_item = next(self.iterator)
        message = get_progress_message(next_item)
        if message:
            click.echo(message)
        return next_item


class GHSearch:
    def __init__(self, client: github.Github, filters: List[Callable], verbose: bool = False):
        self.client = client
        self.filters = filters
        self.verbose = verbose

    def get_filtered_results(self, query):
        results = self.client.search_code(query=query)
        repos = defaultdict(list)

        with self._build_progress_printer(results) as bar:
            for result in bar:
                if self._should_include_result(result):
                    repos[result.repository.full_name].append(result)

        return repos

    def _should_include_result(self, result):
        for result_filter in self.filters:
            if not result_filter(result):
                if self.verbose:
                    click.echo(f"Skipping result for {result.repository.full_name} via {result_filter.__name__}")
                return False
        return True

    def _build_progress_printer(self, results):
        if self.verbose:
            return VerboseProgressPrinter(results)
        return click.progressbar(iterable=results, item_show_func=get_progress_message, bar_template="%(info)s")
