from typing import Callable, Dict, List
from urllib import parse

import click
from github import BadCredentialsException
from github.ContentFile import ContentFile

from ghsearch.client import build_client
from ghsearch.filters import build_content_filter, build_not_archived_filter, build_path_filter
from ghsearch.gh_search import GHSearch


def _print_results(query: str, results: Dict[str, List[ContentFile]]) -> None:
    sorted_results = sorted(results.items(), key=lambda kv: len(kv[1]), reverse=True)

    click.echo("Results:")
    for repo, repo_results in sorted_results:
        repo_result = repo_results[0]
        url = f"{repo_result.repository.html_url}/search?utf8=✓&q={parse.quote(query)}"
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


def run(query, path_filter="", content_filter="", include_archived=False, verbose=False):
    client = build_client()
    try:
        rate_limit = client.get_rate_limit()

        if verbose:
            click.echo(f"Starting with GH Rate limit: {rate_limit.search}")

        filters = _build_filters(path_filter, include_archived, content_filter)
        gh_search = GHSearch(client, filters, verbose)
        results = gh_search.get_filtered_results(query)

        _print_results(query, results)

        if verbose:
            rate_limit = client.get_rate_limit()
            click.echo(f"Ending with GH Rate limit: {rate_limit.search}")
    except BadCredentialsException as e:
        click.echo(f"Bad Credentials: {e}\n\nrun gh-search --help", err=True)


COMMAND_CONTEXT_SETTINGS = {"max_content_width": 120}
COMMAND_HELP = """
GitHub code search using the v3 api.

Relies on GITHUB_TOKEN envar for authentication. Override GitHub API URL via GITHUB_API_URL envar
(defaults to https://api.github.com).

[QUERY] can contain search qualifiers, for example "lookingforthis repo:janeklb/gh-search"
"""


@click.command(help=COMMAND_HELP, context_settings=COMMAND_CONTEXT_SETTINGS)
@click.argument("query")
@click.option("-p", "--path-filter", help="Exclude results whose path (or part of path) does not match this.")
@click.option("-c", "--content-filter", help="Exclude results whose content does not match this.")
@click.option("-a", "--include-archived", help="Include results from archived repos.", default=False, is_flag=True)
@click.option("-v", "--verbose", help="Verbose output.", default=False, is_flag=True)
def cli(*args, **kwargs):
    run(*args, **kwargs)


if __name__ == "__main__":
    cli()
