from collections import defaultdict
from typing import Callable, Dict, List

import click
import github
from click import ClickException
from github.ContentFile import ContentFile
from github.GithubException import GithubException

from ghsearch.terminal import ProgressPrinter


class GHSearch:
    def __init__(self, client: github.Github, filters: List[Callable], verbose: bool = False):
        self.client = client
        self.filters = filters
        self.verbose = verbose

    def get_filtered_results(self, query: List[str]) -> Dict[str, List[ContentFile]]:
        try:
            results = self.client.search_code(query=" ".join(query))
            repos = defaultdict(list)

            with ProgressPrinter(overwrite=not self.verbose) as printer:
                for result in results:
                    printer(f"Checking result for {result.repository.full_name}")
                    exclude_reason = self._should_exclude(result)
                    if not exclude_reason:
                        repos[result.repository.full_name].append(result)
                    elif self.verbose:
                        click.echo(f"Skipping result for {result.repository.full_name} via {exclude_reason}")
        except GithubException as e:
            if e.status == 422:
                message = e.data["message"]
                errors = (
                    [error["message"] for error in e.data["errors"] if isinstance(error, dict)]
                    if e.data["errors"]
                    else []
                )
                raise ClickException(f"{message} (GitHub Exception): {', '.join(errors)}")
            raise e

        return repos

    def _should_exclude(self, result):
        for result_filter in self.filters:
            if not result_filter(result):
                return result_filter.__name__
        return False
