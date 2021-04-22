from typing import Dict, List
from urllib import parse

import click
from click import UsageError
from github.ContentFile import ContentFile
from github.GithubException import BadCredentialsException, GithubException

from ghsearch.client import build_client
from ghsearch.filters import ContentFilter, Filter, NotArchivedFilter, PathFilter
from ghsearch.gh_search import GHSearch


def _sanitize_qualifiers_for_search_url(query: List[str]) -> List[str]:
    return [q for q in query if not (q.startswith("repo:") or q.startswith("org:"))]


def _print_repo_names_only(results: Dict[str, List[ContentFile]]) -> None:
    for repo in results:
        click.echo(repo)


def _print_results(query: List[str], results: Dict[str, List[ContentFile]]) -> None:
    if len(results) == 0:
        click.echo("No results!")
        click.echo(
            "(For limitations of GitHub's code search see https://docs.github.com/en/github/"
            "searching-for-information-on-github/searching-code#considerations-for-code-search)"
        )
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


def _build_filters(path_filter: str = None, include_archived: bool = True, content_filter: str = None) -> List[Filter]:
    filters: List[Filter] = []
    if path_filter:
        filters.append(PathFilter(path_filter))
    if not include_archived:
        filters.append(NotArchivedFilter())
    if content_filter:
        filters.append(ContentFilter(content_filter))
    return filters


def run(
    query: List[str],
    github_token: str,
    github_api_url: str = None,
    path_filter: str = "",
    content_filter: str = "",
    include_archived: bool = False,
    repos_with_matches: bool = False,
    verbose: bool = False,
) -> None:
    client = build_client(github_token, github_api_url)
    try:
        filters = _build_filters(path_filter, include_archived, content_filter)
        gh_search = GHSearch(client, filters, verbose)
        results = gh_search.get_filtered_results(query)

        if repos_with_matches:
            _print_repo_names_only(results)
        else:
            _print_results(query, results)

    except BadCredentialsException as ex:
        raise UsageError(f"Bad Credentials: {ex}", click.get_current_context(silent=True))
    except GithubException as ex:
        if ex.status == 422 and isinstance(ex.data, dict):
            message = ex.data["message"]
            errors = ", ".join(err["message"] for err in ex.data.get("errors", []) if isinstance(err, dict))
            raise UsageError(f"{message} (GitHub Exception): {errors}", click.get_current_context(silent=True))
        raise ex
