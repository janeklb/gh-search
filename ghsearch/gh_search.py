from collections import defaultdict
from typing import Dict, List

import click
import github
from github.ContentFile import ContentFile
from github.Rate import Rate
from github.RateLimit import RateLimit

from ghsearch.filters import Filter, FilterException
from ghsearch.terminal import ProgressPrinter

CORE_CALLS_RELATIVE_LIMIT = 0.1
CORE_CALLS_ABSOLUTE_LIMIT = 500


def _confirm_continue_many_calls(core_rate: Rate, num_results: int, calls_per_res: int) -> None:
    click.confirm(
        f"""
Warning: you are about to potentially make more than {CORE_CALLS_ABSOLUTE_LIMIT} core api requests.
Your search yielded {num_results} results, and gh-search may make up to {calls_per_res} core api call(s) per result.

Your current core api usage is {core_rate.remaining}/{core_rate.limit} (resets {core_rate.reset})

Do you want to continue?""".strip(),
        abort=True,
    )


def _confirm_continue_near_limit(core_rate: Rate, num_results: int, calls_per_res: int) -> None:
    click.confirm(
        f"""
Warning: you are at risk of going below {CORE_CALLS_RELATIVE_LIMIT:.0%} of your remaining core api rate limit.
Your search yielded {num_results} results, and gh-search may make up to {calls_per_res} core api call(s) per result.

Your current core api usage is {core_rate.remaining}/{core_rate.limit} (resets {core_rate.reset})

Do you want to continue?""".strip(),
        abort=True,
    )


def _echo_rate_limits(rate_limit: RateLimit) -> None:
    click.echo(
        f"Core rate limit: {rate_limit.core.remaining}/{rate_limit.core.limit} (resets {rate_limit.core.reset}), "
        f"Search rate limit: {rate_limit.search.remaining}/{rate_limit.search.limit} (resets {rate_limit.search.reset})"
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
                try:
                    exclude_reason = self._should_exclude(result)
                except FilterException as e:
                    printer(str(e), force=True)
                else:
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

            num_core_api_calls_worst_case = num_results * max_core_api_calls_per_result
            remaining_worst_case = core_rate.remaining - num_core_api_calls_worst_case
            if remaining_worst_case / core_rate.limit < CORE_CALLS_RELATIVE_LIMIT:
                _confirm_continue_near_limit(core_rate, num_results, max_core_api_calls_per_result)
            elif num_core_api_calls_worst_case > CORE_CALLS_ABSOLUTE_LIMIT:
                _confirm_continue_many_calls(core_rate, num_results, max_core_api_calls_per_result)
