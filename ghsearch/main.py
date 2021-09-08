from typing import List

import click
from click import UsageError
from github.GithubException import BadCredentialsException, GithubException

from ghsearch.client import build_client
from ghsearch.filters import ContentFilter, Filter, FilterException, NotArchivedFilter, PathFilter, RegexContentFilter
from ghsearch.gh_search import GHSearch
from ghsearch.output import Printer


def _build_filters(
    path_filter: str = None, include_archived: bool = True, content_filter: str = None, regex_content_filter: str = None
) -> List[Filter]:
    filters: List[Filter] = []
    if path_filter:
        filters.append(PathFilter(path_filter))
    if not include_archived:
        filters.append(NotArchivedFilter())
    if content_filter:
        filters.append(ContentFilter(content_filter))
    if regex_content_filter:
        filters.append(RegexContentFilter(regex_content_filter))
    return filters


def run(
    query: List[str],
    github_token: str,
    printer: Printer,
    github_api_url: str = None,
    path_filter: str = None,
    content_filter: str = None,
    regex_content_filter: str = None,
    include_archived: bool = False,
    verbose: bool = False,
) -> None:
    client = build_client(github_token, github_api_url)

    try:
        filters = _build_filters(path_filter, include_archived, content_filter, regex_content_filter)
    except FilterException as ex:
        raise UsageError(str(ex), click.get_current_context(silent=True))

    try:
        gh_search = GHSearch(client, filters, verbose)
        results = gh_search.get_filtered_results(query)

        printer.print(query, results)

    except BadCredentialsException as ex:
        raise UsageError(f"Bad Credentials: {ex}", click.get_current_context(silent=True))
    except GithubException as ex:
        if ex.status == 422 and isinstance(ex.data, dict):
            message = ex.data["message"]
            errors = ", ".join(err["message"] for err in ex.data.get("errors", []) if isinstance(err, dict))
            raise UsageError(f"{message} (GitHub Exception): {errors}", click.get_current_context(silent=True))
        raise ex
