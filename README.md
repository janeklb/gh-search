# gh-search

GitHub code search from your cli

## Features

* All features of [GitHub Search API](https://docs.github.com/en/free-pro-team@latest/rest/reference/search#search-code) (eg. search qualifiers)
* Apply filters on the GitHub Search API response (eg. ignore archived repos or search for additional text in matched content)
* View search results grouped by repo
* Works with GitHub Enterprise

## Installation

```bash
pip install gh-search
```

## Usage

**IMPORTANT**: This tool requires that you GitHub token set on the `GITHUB_TOKEN` envvar (or passed to the script via the `--github-token` option).

Invoke with `gh-search` and pass a query string as the first argument. For example, to search for the string "usage" in this repo:
```bash
gh-search usage repo:janeklb/gh-search
```

_Note that `repo:` is a search qualifier natively supported by the GitHub Search API._

`gh-search` also offers the following options

- `-a`/`--include-archived`: include results from archived repos (default behaviour is to exclude results from archived repositories).
- `-p TEXT`/`--path-filter TEXT`: similar to the `path:` search qualifier, but a bit more flexible as it does a string match on the path (rather than relying on GitHub's indexed path components). For example `-p cat` will show matches against a file called `mycat.json` whereas `path:cat` will not.
- `-c TEXT`/`--content-filter TEXT`: applies a string match on the content of a search result. A bit more flexible than specifying an additional search term in the search query, tests for a string match directly on the text content rather than relying on how GitHub has indexed a file for searching.
- `-v`: verbose output, print information about the repos being scanned and ignored via filters

### Enterprise

If you want to search against GitHub Enterprise set the `GITHUB_API_URL` envvar with a URL to the v3 api endpoint. eg. `GITHUB_API_URL=https://git.mycompany.net/api/v3`. You can also use the `--github-api-url` option for this.

## Developing

- `make install-dev` install dev dependencies (set up your own virtual environment first)
- `make unit` run unit tests
- `make lint` run linters
