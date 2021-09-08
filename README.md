# gh-search

GitHub code search with full text regex filtering, from your cli.

## Features

* Filters search results (eg. ignore archived repositories or search for specific text in matched content)
* Displays results grouped by `organisation/repository`
* GitHub API rate limit aware (prevent accidentally consuming your entire core API quota)
* Uses GitHub's [Rest API] (and therefore works with GitHub Enterprise)

[Rest API]: https://docs.github.com/en/rest/reference/search#search-code

## Installation

`gh-search` is available as a python package via [pypi.org](https://pypi.org/project/gh-search/) and requires Python 3.6+

```bash
pip install gh-search
```

## Authentication

A valid GitHub personal access token, with the `repo` scope, is required to retrieve search results.
It can be set on a `GITHUB_TOKEN` envvar or passed to the script via the `--github-token` option.

### Enterprise

To search GitHub Enterprise set the `GITHUB_API_URL` envvar to your organisation's GitHub v3 API endpoint.
eg. `GITHUB_API_URL=https://github.mycompany.net/api/v3`. You can also use the `--github-api-url` option for this.


## Usage

Invoke with `gh-search` and pass a query string as the first argument. For example, to search for the word "usage" in this repo:
```bash
gh-search usage repo:janeklb/gh-search
```

_Note that `repo:` is a search qualifier natively supported by the GitHub Search API. See GitHub's [searching code] documentation to see what other qualifiers are available._

### Example: regex content filtering

If you are searching for a specific non-alphanumeric string you can use the `--regex-content-filter` (or `--content-filter`) options. This _must_
be combined with a valid GitHub Search API query (which will produce the result set that will subsequently be filtered).

For example if you're looking for a `special_var` variable being set to a value  of characters beginning with `10` you could do something like:

```bash
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
