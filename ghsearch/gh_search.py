from collections import defaultdict
from typing import Dict, List

import click
import github
from github.ContentFile import ContentFile
from github.RateLimit import RateLimit

from ghsearch.filters import Filter
from ghsearch.terminal import ProgressPrinter


def _echo_rate_limits(rate_limit: RateLimit) -> None:
    click.echo(
        f"Rate limits:"
        f" {rate_limit.search.remaining}/{rate_limit.search.limit} (search, resets {rate_limit.search.reset}),"
        f" {rate_limit.core.remaining}/{rate_limit.core.limit} (core, resets {rate_limit.core.reset})"
    )


class GHSearch:
    def __init__(self, client: github.Github, filters: List[Filter], verbose: bool = False):
        self.client = client
        self.filters = filters
        self.verbose = verbose

    def get_filtered_results(self, query: List[str]) -> Dict[str, List[ContentFile]]:
        rate_limit = self.client.get_rate_limit()
        if self.verbose:
            _echo_rate_limits(rate_limit)

        results = self.client.search_code(query=" ".join(query))
        repos = defaultdict(list)

        with ProgressPrinter(overwrite=not self.verbose) as printer:
            for result in results:
                printer(f"Checking result for {result.repository.full_name}")
                exclude_reason = self._should_exclude(result)
                if not exclude_reason:
                    repos[result.repository.full_name].append(result)
                elif self.verbose:
                    click.echo(f"Skipping result for {result.repository.full_name} via {exclude_reason}")

        if self.verbose:
            _echo_rate_limits(self.client.get_rate_limit())

        return repos

    def _should_exclude(self, result):
        for result_filter in self.filters:
            if not result_filter(result):
                return result_filter.__class__.__name__
        return False
