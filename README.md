<!-- markdownlint-disable MD004 -->

# gh-search

[![Last release](https://img.shields.io/pypi/v/gh-search.svg)](https://pypi.python.org/pypi/gh-search)
[![Python versions](https://img.shields.io/pypi/pyversions/gh-search.svg)](https://pypi.python.org/pypi/gh-search)
[![Unittests status](https://github.com/janeklb/gh-search/actions/workflows/lint-and-test.yml/badge.svg?branch=main)](https://github.com/janeklb/gh-search/actions/workflows/lint-and-test.yml?query=branch%3Amain)

GitHub code search with full text regex filtering, from your cli.

## Features

- Filters search results (eg. ignore archived repositories or search for specific text in matched content)
- Displays results grouped by `organisation/repository`
- GitHub API rate limit aware (prevent accidentally consuming your entire core API quota)
- Uses GitHub's [Rest API] (and therefore works with GitHub Enterprise)

[Rest API]: https://docs.github.com/en/rest/reference/search#search-code

## Installation

`gh-search` is available as a python package via [pypi.org](https://pypi.org/project/gh-search/) and requires Python 3.12+

```bash
pipx install gh-search
```

## Authentication

A valid GitHub personal access token, with the `repo` scope, is required to retrieve search results.
It can be set on a `GITHUB_TOKEN` envvar or passed to the script via the `--github-token` option.

### Enterprise

To search GitHub Enterprise set the `GITHUB_API_URL` envvar to your organisation's GitHub v3 API endpoint.
eg. `GITHUB_API_URL=https://github.mycompany.net/api/v3`. You can also use the `--github-api-url` option for this.

## Usage

Invoke with `gh-search` and pass a query string as the first argument. For example, to search for the word "usage" in this repo:

```shell
gh-search usage repo:janeklb/gh-search
```

_Note that `repo:` is a search qualifier natively supported by the GitHub Search API. See GitHub's [searching code] documentation to see what other qualifiers are available._

### Example: regex content filtering

If you are searching for a specific non-alphanumeric string you can use the `--regex-content-filter` (or `--content-filter`) options. This _must_
be combined with a valid GitHub Search API query (which will produce the result set that will subsequently be filtered).

For example if you're looking for a `special_var` variable being set to a value of characters beginning with `10` you could do something like:

```shell
gh-search special_var -e "special_var\\s*=\\s*10"
```

### All available options

```text
Usage: gh-search [OPTIONS] QUERY...

  QUERY must contain at least one search term, but may also contain search qualifiers
  (https://docs.github.com/en/github/searching-for-information-on-github/searching-code)

Options:
  --github-token TEXT             GitHub Auth Token. Will fall back on GITHUB_TOKEN envvar.
  --github-api-url TEXT           Override default GitHub API URL. Can also specify via GITHUB_API_URL envvar.
  -p, --path-filter TEXT          Exclude results whose path (or part of path) does not match this.
  -c, --content-filter TEXT       Exclude results whose content does not match this.
  -e, --regex-content-filter TEXT
                                  Exclude results whose content does not match this regex.
  -a, --include-archived          Include results from archived repos.
  -l, --repos-with-matches        Only the names of repos are printed. Equivalent to --output=repo-list
  -o, --output TEXT               Output style; one of: default, repo-list, json, yaml
  -v, --verbose                   Verbose output.
  --help                          Show this message and exit.
```

### Saving default configuration values to disk

Default values for options can specified via a config file. Location of this file is based on
[`click.get_app_dir`](https://click.palletsprojects.com/en/8.0.x/api/#click.get_app_dir), with
`gh-search` as the `app_name` (eg. `~/Library/Application\ Support/gh-search/config` on MacOS).
You'll see the exact file location printed out next to the help text of the `--config` of
`gh-search --help` (or if you run with the `--verbose` flag).

The option names must be converted to snake_case as per [`click`][click]'s parameter naming.

For example, in order set a default `--github-token` and `--github-api-url` you would write the
following to your config file (replacing `<PLACE HOLDERS>` accordingly):

```config
github_token="<YOUR TOKEN>"
github_api_url="<THE API URL>"
```

### Rate Limiting

`gh-search` checks your [rate limits] and will prompt you to continue if your search might:

- perform more than `500` core API requests
- leave you with less than `10%` of your core API quota

Only the **core** API quota is checked because `gh-search`'s filters can make heavy use it. The **search** API quota is _not_ checked.

## Developing

- `make install-dev` install dev dependencies (set up your own virtual environment first)
- `make unit` run unit tests
- `make lint` run linters

[searching code]: https://docs.github.com/en/github/searching-for-information-on-github/searching-code
[rate limits]: https://docs.github.com/en/rest/reference/rate-limit
[click]: https://click.palletsprojects.com/
