from collections import defaultdict
from typing import Dict, List

import click
import github
from github.ContentFile import ContentFile
from github.Rate import Rate
from github.RateLimit import RateLimit

from ghsearch.filters import Filter
from ghsearch.terminal import ProgressPrinter

CORE_LIMIT_THRESHOLD = 0.1
CORE_LIMIT_WARNING_MESSAGE = """
Warning: you are at risk of using more than the remaining {threshold:.0%} of your core api limit.
Your search yielded {num} results, and each result may trigger up to {calls_per_res} core api call(s) per result.

Your current usage is {remaining}/{limit} (resets at {reset})

Do you want to continue?
"""


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
        self._check_core_limit_threshold(results.totalCount, rate_limit.core)

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

    def _check_core_limit_threshold(self, num_results: int, core_rate: Rate) -> None:
        max_core_api_calls_per_result = sum(bool(f.uses_core_api) for f in self.filters)
        if max_core_api_calls_per_result > 0:

            remaining_worst_case = core_rate.remaining - (num_results * max_core_api_calls_per_result)
            if remaining_worst_case / core_rate.limit < CORE_LIMIT_THRESHOLD:
                click.confirm(
                    CORE_LIMIT_WARNING_MESSAGE.format(
                        threshold=CORE_LIMIT_THRESHOLD,
                        reset=core_rate.reset,
                        limit=core_rate.limit,
                        remaining=core_rate.remaining,
                        num=num_results,
                        calls_per_res=max_core_api_calls_per_result,
                    ).strip(),
                    abort=True,
                )
