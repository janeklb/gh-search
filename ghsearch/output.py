from collections import defaultdict
from typing import Dict, List, Type
from urllib import parse

import click
from github.ContentFile import ContentFile


class Printer:
    @staticmethod
    def sanitize_qualifiers_for_search_url(query: List[str]) -> List[str]:
        return [q for q in query if not (q.startswith("repo:") or q.startswith("org:"))]

    def print(self, query: List[str], results: List[ContentFile]) -> None:
        results_per_repo = defaultdict(list)
        for result in results:
            results_per_repo[result.repository.full_name].append(result)
        return self._print(query, results_per_repo)

    def _print(self, query: List[str], results_per_repo: Dict[str, List[ContentFile]]) -> None:
        raise NotImplementedError()


_REGISTRY: Dict[str, Type[Printer]] = {}


def register_printer(cls: Type[Printer]) -> Type[Printer]:
    name = getattr(cls, "NAME", False)
    if not isinstance(name, str):
        raise NotImplementedError(f"{cls.__name__} must declare a NAME property")
    if name in _REGISTRY:
        raise IndexError(f"Printer {name} is already registered")
    _REGISTRY[name] = cls
    return cls


def printers_list() -> List[str]:
    return list(_REGISTRY.keys())


def printer_factory(name: str, force_repo_list_printer: bool = False) -> Printer:
    if force_repo_list_printer:
        return RepoListPrinter()
    return _REGISTRY[name]()


@register_printer
class DefaultPrinter(Printer):
    NAME = "default"

    def _print(self, query: List[str], results_per_repo: Dict[str, List[ContentFile]]) -> None:
        if len(results_per_repo) == 0:
            click.echo("No results!")
            click.echo(
                "(For limitations of GitHub's code search see https://docs.github.com/en/github/"
                "searching-for-information-on-github/searching-code#considerations-for-code-search)"
            )
            return

        sorted_results = sorted(results_per_repo.items(), key=lambda kv: len(kv[1]), reverse=True)

        q_param = parse.quote(" ".join(self.sanitize_qualifiers_for_search_url(query)))
        click.echo("Results:")
        for repo, repo_results in sorted_results:
            repo_result = repo_results[0]
            url = f"{repo_result.repository.html_url}/search?utf8=✓&q={q_param}"
            click.echo(f" {len(repo_results)} - {repo}: {url}")

            repo_results.sort(key=lambda x: x.path)
            for result in repo_results:
                click.echo(f"\t- {result.path}")


@register_printer
class RepoListPrinter(Printer):
    NAME = "repo-list"

    def _print(self, query: List[str], results_per_repo: Dict[str, List[ContentFile]]) -> None:
        for repo in results_per_repo:
            click.echo(repo)
