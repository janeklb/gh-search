from typing import Callable, Dict, List
from urllib import parse

import click
from github import BadCredentialsException
from github.ContentFile import ContentFile

from ghsearch.client import build_client
from ghsearch.filters import build_content_filter, build_not_archived_filter, build_path_filter
from ghsearch.gh_search import GHSearch


def _sanitize_qualifiers_for_search_url(query: List[str]) -> List[str]:
    return [q for q in query if not (q.startswith("repo:") or q.startswith("org:"))]


def _print_results(query: List[str], results: Dict[str, List[ContentFile]]) -> None:
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


def _create_none_value_validator(message):
    def _validator(ctx, param, value):
        if value is None:
            raise click.UsageError(message, ctx=ctx)
        return value

    return _validator


def _ensure_search_term(ctx, param, value):
    if any(":" not in word for word in value):
        return value
    raise click.UsageError("QUERY must contain at least one search term", ctx=ctx)


@click.command(
    help="QUERY must contain at least one search term, but may also contain search qualifiers"
    " (https://docs.github.com/en/github/searching-for-information-on-github/searching-code)",
    context_settings={"max_content_width": 120},
)
@click.argument("QUERY", nargs=-1, required=True, callback=_ensure_search_term)
@click.option(
    "--github-token",
    envvar="GITHUB_TOKEN",
    help="GitHub Auth Token. Will fall back on GITHUB_TOKEN envvar.",
    callback=_create_none_value_validator("GitHub token must be set via --github-token option or GITHUB_TOKEN envvar."),
)
@click.option(
    "--github-api-url",
    envvar="GITHUB_API_URL",
    help="Override default GitHub API URL. Can also specify via GITHUB_API_URL envvar.",
)
@click.option("-p", "--path-filter", help="Exclude results whose path (or part of path) does not match this.")
@click.option("-c", "--content-filter", help="Exclude results whose content does not match this.")
@click.option("-a", "--include-archived", help="Include results from archived repos.", default=False, is_flag=True)
@click.option("-v", "--verbose", help="Verbose output.", default=False, is_flag=True)
def cli(*args, **kwargs):
    run(*args, **kwargs)


if __name__ == "__main__":
    cli()
