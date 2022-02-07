from collections import defaultdict
from typing import IO, Dict, List, Type
from urllib import parse

from github.ContentFile import ContentFile


class Printer:
    @staticmethod
    def sanitize_qualifiers_for_search_url(query: List[str]) -> List[str]:
        return [q for q in query if not (q.startswith("repo:") or q.startswith("org:"))]

    def __init__(self, stream: IO) -> None:
        self._stream = stream

    def print(self, query: List[str], results: List[ContentFile]) -> None:
        results_per_repo = defaultdict(list)
        for result in results:
            results_per_repo[result.repository.full_name].append(result)
        self._print(query, results_per_repo)
        self._stream.flush()

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


def printer_factory(name: str, stream: IO, force_repo_list_printer: bool = False) -> Printer:
    if force_repo_list_printer:
        return RepoListPrinter(stream)
    return _REGISTRY[name](stream)


@register_printer
class DefaultPrinter(Printer):
    NAME = "default"

    def _print(self, query: List[str], results_per_repo: Dict[str, List[ContentFile]]) -> None:
        if len(results_per_repo) == 0:
            self._stream.write("No results!\n")
            self._stream.write(
                "(For limitations of GitHub's code search see https://docs.github.com/en/github/"
                "searching-for-information-on-github/searching-code#considerations-for-code-search)\n"
            )
            return

        sorted_results = sorted(results_per_repo.items(), key=lambda kv: len(kv[1]), reverse=True)

        q_param = parse.quote(" ".join(self.sanitize_qualifiers_for_search_url(query)))
        self._stream.write("Results:\n")
        for repo, repo_results in sorted_results:
            repo_result = repo_results[0]
            url = f"{repo_result.repository.html_url}/search?utf8=✓&q={q_param}"
            self._stream.write(f" {len(repo_results)} - {repo}: {url}\n")

            repo_results.sort(key=lambda x: x.path)
            for result in repo_results:
                self._stream.write(f"\t- {result.path}\n")


@register_printer
class RepoListPrinter(Printer):
    NAME = "repo-list"

    def _print(self, query: List[str], results_per_repo: Dict[str, List[ContentFile]]) -> None:
        for repo in results_per_repo:
            self._stream.write(repo + "\n")


class StructuredPrinter(Printer):
    def _print(self, query: List[str], results_per_repo: Dict[str, List[ContentFile]]) -> None:
        self._print_serialise([self._build_repo_results(results_per_repo[repo]) for repo in results_per_repo])

    @classmethod
    def _build_repo_results(cls, results: List[ContentFile]) -> Dict:
        repo = results[0].repository
        return {
            "full_name": repo.full_name,
            "html_url": repo.html_url,
            "fork": repo.fork,
            "owner": repo.owner.login,
            "name": repo.name,
            "results": cls._build_results(results),
        }

    @classmethod
    def _build_results(cls, results: List[ContentFile]) -> List[Dict]:
        return [cls._build_result(result) for result in results]

    @staticmethod
    def _build_result(result: ContentFile) -> Dict:
        return {
            "path": result.path,
            "name": result.name,
            "size": result.size,
            "html_url": result.html_url,
        }

    def _print_serialise(self, structured_results: List[Dict]) -> None:
        raise NotImplementedError()


@register_printer
class JsonPrinter(StructuredPrinter):
    NAME = "json"

    def _print_serialise(self, structured_results: List[Dict]) -> None:
        import json

        json.dump(structured_results, fp=self._stream)


@register_printer
class YamlPrinter(StructuredPrinter):
    NAME = "yaml"

    def _print_serialise(self, structured_results: List[Dict]) -> None:
        from ruamel.yaml import YAML

        yaml = YAML(typ="safe", pure=True)
        yaml.default_flow_style = False
        yaml.dump(structured_results, stream=self._stream)
