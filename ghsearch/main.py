from typing import Callable, Dict, List
from urllib import parse

import click
from click import UsageError
from github.ContentFile import ContentFile
from github.GithubException import BadCredentialsException, GithubException

from ghsearch.client import build_client
from ghsearch.filters import build_content_filter, build_not_archived_filter, build_path_filter
from ghsearch.gh_search import GHSearch


def _sanitize_qualifiers_for_search_url(query: List[str]) -> List[str]:
    return [q for q in query if not (q.startswith("repo:") or q.startswith("org:"))]


def _print_results(query: List[str], results: Dict[str, List[ContentFile]]) -> None:
    if len(results) == 0:
        click.echo("No results!")
        return
    sorted_results = sorted(results.items(), key=lambda kv: len(kv[1]), reverse=True)

    q_param = parse.quote(" ".join(_sanitize_qualifiers_for_search_url(query)))
    click.echo("Results:")
    for repo, repo_results in sorted_results:
        repo_result = repo_results[0]
        url = f"{repo_result.repository.html_url}/search?utf8=✓&q={q_param}"
        click.echo(f" {len(repo_results)} - {repo}: {url}")

        repo_results.sort(key=lambda x: x.path)
        for result in repo_results:
            click.echo(f"\t- {result.path}")


def _build_filters(
    path_filter: str = None, include_archived: bool = True, content_filter: str = None
) -> List[Callable]:
    filters = []
    if path_filter:
        filters.append(build_path_filter(path_filter))
    if not include_archived:
        filters.append(build_not_archived_filter())
    if content_filter:
        filters.append(build_content_filter(content_filter))
    return filters


def run(
    query: List[str],
    github_token: str,
    github_api_url: str = None,
    path_filter: str = "",
    content_filter: str = "",
    include_archived: bool = False,
    verbose: bool = False,
) -> None:
    client = build_client(github_token, github_api_url)
    try:
        if verbose:
            rate_limit = client.get_rate_limit()
            click.echo(f"GH Rate limits: search={rate_limit.search}, core={rate_limit.core}")

        filters = _build_filters(path_filter, include_archived, content_filter)
        gh_search = GHSearch(client, filters, verbose)
        results = gh_search.get_filtered_results(query)

        _print_results(query, results)

        if verbose:
            rate_limit = client.get_rate_limit()
            click.echo(f"GH Rate limits: search={rate_limit.search}, core={rate_limit.core}")
    except BadCredentialsException as ex:
        raise UsageError(f"Bad Credentials: {ex}", click.get_current_context(silent=True))
    except GithubException as ex:
        if ex.status == 422 and isinstance(ex.data, dict):
            message = ex.data["message"]
            errors = ", ".join(err["message"] for err in ex.data.get("errors", []) if isinstance(err, dict))
            raise UsageError(f"{message} (GitHub Exception): {errors}", click.get_current_context(silent=True))
        raise ex
