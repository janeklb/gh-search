from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterator, List

import click
import github
from github.ContentFile import ContentFile
from github.GithubException import GithubException, RateLimitExceededException
from github.Rate import Rate
from github.RateLimit import RateLimit

from ghsearch.filters import Filter, FilterException
from ghsearch.terminal import ProgressPrinter

CORE_CALLS_RELATIVE_LIMIT = 0.1
CORE_CALLS_ABSOLUTE_LIMIT = 500
MAX_SEARCH_RESULTS = 1000
RESULTS_PER_PAGE = 100


@dataclass
class SearchRateLimit:
    remaining: int | None
    reset: datetime | None


@dataclass
class CodeSearchPage:
    results: List[ContentFile]
    total_count: int
    incomplete_results: bool
    rate_limit: SearchRateLimit
    has_next_page: bool
    reached_result_ceiling: bool


@dataclass
class SearchOutcome:
    results: List[ContentFile] = field(default_factory=list)
    total_count: int = 0
    retrieved_count: int = 0
    truncated: bool = False
    truncation_reason: str | None = None
    search_rate_limit: SearchRateLimit | None = None


class CodeSearchRateLimitError(Exception):
    def __init__(self, rate_limit: SearchRateLimit):
        self.rate_limit = rate_limit


class CodeSearchPaginator:
    def __init__(self, client: github.Github):
        self.client = client
        # PyGithub does not expose code-search response metadata publicly.
        self.requester = getattr(client, "_Github__requester")

    @staticmethod
    def _rate_limit_from_headers(headers: Dict[str, str]) -> SearchRateLimit:
        remaining = headers.get("x-ratelimit-remaining")
        reset = headers.get("x-ratelimit-reset")
        return SearchRateLimit(
            remaining=int(remaining) if remaining is not None else None,
            reset=datetime.fromtimestamp(int(reset), tz=timezone.utc) if reset is not None else None,
        )

    def pages(self, query: str) -> Iterator[CodeSearchPage]:
        page = 1
        retrieved_count = 0

        while True:
            try:
                headers, data = self.requester.requestJsonAndCheck(
                    "GET",
                    "/search/code",
                    parameters={"q": query, "page": page, "per_page": RESULTS_PER_PAGE},
                )
            except RateLimitExceededException as ex:
                raise CodeSearchRateLimitError(self._rate_limit_from_headers(ex.headers or {})) from ex

            results = [self.client.create_from_raw_data(ContentFile, result, headers) for result in data["items"]]
            retrieved_count += len(results)
            total_count = data["total_count"]
            rate_limit = self._rate_limit_from_headers(headers)
            has_next_page = 'rel="next"' in headers.get("link", "")
            reached_result_ceiling = retrieved_count >= MAX_SEARCH_RESULTS and total_count > MAX_SEARCH_RESULTS
            yield CodeSearchPage(
                results=results,
                total_count=total_count,
                incomplete_results=data.get("incomplete_results", False),
                rate_limit=rate_limit,
                has_next_page=has_next_page,
                reached_result_ceiling=reached_result_ceiling,
            )

            if not has_next_page or reached_result_ceiling or rate_limit.remaining == 0:
                return
            page += 1


def _confirm_continue_many_calls(core_rate: Rate, num_results: int, calls_per_res: int) -> None:
    click.confirm(
        f"""
Warning: you are about to potentially make more than {CORE_CALLS_ABSOLUTE_LIMIT} core api requests.
Your search yielded {num_results} results, and gh-search may make up to {calls_per_res} core api call(s) per result.

Your current core api usage is {core_rate.remaining}/{core_rate.limit} (resets {core_rate.reset})

Do you want to continue?""".strip(),
        abort=True,
        err=True,
    )


def _confirm_continue_near_limit(core_rate: Rate, num_results: int, calls_per_res: int) -> None:
    click.confirm(
        f"""
Warning: you are at risk of going below {CORE_CALLS_RELATIVE_LIMIT:.0%} of your remaining core api rate limit.
Your search yielded {num_results} results, and gh-search may make up to {calls_per_res} core api call(s) per result.

Your current core api usage is {core_rate.remaining}/{core_rate.limit} (resets {core_rate.reset})

Do you want to continue?""".strip(),
        abort=True,
        err=True,
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

    def get_rate_limit(self) -> RateLimit | None:
        try:
            return self.client.get_rate_limit()
        except GithubException as ge:
            # 404 means that rate limiting is disabled
            if ge.status == 404:
                return None
            raise ge

    def get_filtered_results(self, query: List[str], max_results: int | None = None) -> SearchOutcome:
        rate_limit = self.get_rate_limit()

        if rate_limit and self.verbose:
            _echo_rate_limits(rate_limit)

        outcome = SearchOutcome()
        paginator = CodeSearchPaginator(self.client)

        with ProgressPrinter(overwrite=not self.verbose) as printer:
            for page in paginator.pages(" ".join(query)):
                outcome.total_count = page.total_count
                outcome.search_rate_limit = page.rate_limit
                outcome.retrieved_count += len(page.results)

                if rate_limit:
                    self._check_core_limit_threshold(page.total_count, rate_limit.core)
                    rate_limit = None

                for result in page.results:
                    printer(f"Checking result for {result.repository.full_name}")
                    try:
                        exclude_reason = self._should_exclude(result)
                    except FilterException as e:
                        printer(str(e), force=True)
                    else:
                        if not exclude_reason:
                            outcome.results.append(result)
                            if max_results is not None and len(outcome.results) >= max_results:
                                outcome.truncated = True
                                outcome.truncation_reason = "max_results"
                                return outcome
                        elif self.verbose:
                            click.echo(f"Skipping result for {result.repository.full_name} via {exclude_reason}")

                if page.incomplete_results:
                    outcome.truncated = True
                    outcome.truncation_reason = "incomplete_results"
                if page.reached_result_ceiling:
                    outcome.truncated = True
                    outcome.truncation_reason = "result_ceiling"
                if page.has_next_page and page.rate_limit.remaining == 0:
                    outcome.truncated = True
                    outcome.truncation_reason = "rate_limit"

        rate_limit = self.get_rate_limit()
        if rate_limit and self.verbose:
            _echo_rate_limits(rate_limit)

        return outcome

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
