import click

from ghsearch.main import run
from ghsearch.output import Printer, printer_factory, printers_list


def _printer(ctx: click.Context, param: click.Parameter, value: str) -> Printer:
    try:
        force_repo_printer = bool(ctx.params.get("repos_with_matches"))
        return printer_factory(value, force_repo_printer)
    except KeyError:
        raise click.BadParameter(f"Must be one of: {', '.join(printers_list())}", ctx=ctx, param=param)


def _create_none_value_validator(message):
    def _validator(ctx, _, value):
        if value is None:
            raise click.UsageError(message, ctx=ctx)
        return value

    return _validator


@click.command(
    help="QUERY must contain at least one search term, but may also contain search qualifiers"
    " (https://docs.github.com/en/github/searching-for-information-on-github/searching-code)",
    context_settings={"max_content_width": 120},
)
@click.argument("QUERY", nargs=-1, required=True)
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
@click.option("-e", "--regex-content-filter", help="Exclude results whose content does not match this regex.")
@click.option("-a", "--include-archived", help="Include results from archived repos.", default=False, is_flag=True)
@click.option(
    "-l",
    "--repos-with-matches",
    help="Only the names of repos are printed. Equivalent to --output=repo-list",
    default=False,
    is_flag=True,
)
@click.option(
    "-o", "--output", help=f"Output style; one of: {', '.join(printers_list())}", callback=_printer, default="default"
)
@click.option("-v", "--verbose", help="Verbose output.", default=False, is_flag=True)
def cli(
    query,
    output,
    include_archived,
    verbose,
    github_token,
    github_api_url=None,
    path_filter=None,
    context_filter=None,
    regex_context_filter=None,
    **_,
):
    run(
        query=query,
        github_token=github_token,
        printer=output,
        github_api_url=github_api_url,
        path_filter=path_filter,
        content_filter=context_filter,
        regex_content_filter=regex_context_filter,
        include_archived=include_archived,
        verbose=verbose,
    )


if __name__ == "__main__":
    cli()
