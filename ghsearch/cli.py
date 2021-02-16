import click

from ghsearch.main import run


def _create_none_value_validator(message):
    def _validator(ctx, param, value):
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
@click.option("-a", "--include-archived", help="Include results from archived repos.", default=False, is_flag=True)
@click.option("-l", "--repos-with-matches", help="Only the names of repos are printed.", default=False, is_flag=True)
@click.option("-v", "--verbose", help="Verbose output.", default=False, is_flag=True)
def cli(*args, **kwargs):
    run(*args, **kwargs)


if __name__ == "__main__":
    cli()
