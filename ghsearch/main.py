from typing import List

import click
from click import UsageError
from github.GithubException import BadCredentialsException, GithubException

from ghsearch.client import build_client
from ghsearch.filters import ContentFilter, Filter, FilterException, PathFilter, RegexContentFilter
from ghsearch.gh_search import (
    TRUNCATION_REASON_INCOMPLETE_RESULTS,
    TRUNCATION_REASON_RATE_LIMIT,
    TRUNCATION_REASON_RESULT_CEILING,
    CodeSearchRateLimitError,
    GHSearch,
    SearchOutcome,
)
from ghsearch.output import Printer


def _build_filters(
    path_filter: str | None = None,
    content_filter: str | None = None,
    regex_content_filter: str | None = None,
) -> List[Filter]:
    filters: List[Filter] = []
    if path_filter:
        filters.append(PathFilter(path_filter))
    if content_filter:
        filters.append(ContentFilter(content_filter))
    if regex_content_filter:
        filters.append(RegexContentFilter(regex_content_filter))
    return filters


def _warn_if_search_is_truncated(outcome: SearchOutcome) -> None:
    if outcome.truncation_reason == TRUNCATION_REASON_INCOMPLETE_RESULTS:
        click.echo("Warning: GitHub reported incomplete code-search results. Narrow the query and retry.", err=True)
    elif outcome.truncation_reason == TRUNCATION_REASON_RESULT_CEILING:
        click.echo("Warning: GitHub returns at most 1,000 code-search results. Narrow the query and retry.", err=True)
    elif outcome.truncation_reason == TRUNCATION_REASON_RATE_LIMIT:
        reset = outcome.search_rate_limit.reset if outcome.search_rate_limit else None
        click.echo(f"Warning: Code-search rate limit exhausted. Retry after {reset}.", err=True)


def run(
    query: List[str],
    github_token: str,
    printer: Printer,
    github_api_url: str | None = None,
    path_filter: str | None = None,
    content_filter: str | None = None,
    regex_content_filter: str | None = None,
    verbose: bool = False,
) -> None:
    client = build_client(github_token, github_api_url)

    try:
        filters = _build_filters(path_filter, content_filter, regex_content_filter)
    except FilterException as ex:
        raise UsageError(str(ex), click.get_current_context(silent=True))

    try:
        gh_search = GHSearch(client, filters, verbose)
        outcome = gh_search.get_filtered_results(query)

        printer.print(query, outcome.results)
        _warn_if_search_is_truncated(outcome)

    except BadCredentialsException as ex:
        raise UsageError(f"Bad Credentials: {ex}", click.get_current_context(silent=True))
    except GithubException as ex:
        if ex.status == 422 and isinstance(ex.data, dict):
            message = ex.data["message"]
            errors = ", ".join(err["message"] for err in ex.data.get("errors", []) if isinstance(err, dict))
            raise UsageError(f"{message} (GitHub Exception): {errors}", click.get_current_context(silent=True))
        raise ex
    except CodeSearchRateLimitError as ex:
        raise UsageError(
            f"GitHub code-search rate limit exhausted. Retry after {ex.rate_limit.reset}.",
            click.get_current_context(silent=True),
        )
