import re

from github.ContentFile import ContentFile
from github.GithubException import GithubException


class FilterException(BaseException):
    def __init__(self, filter, message):
        super().__init__(message)
        self.filter = filter


class Filter:
    """This filter uses the core api"""

    uses_core_api = True

    def __call__(self, result: ContentFile) -> bool:
        raise NotImplementedError


class DecodedContentFilter(Filter):
    def __call__(self, result: ContentFile) -> bool:
        try:
            content = result.decoded_content.decode("utf-8")
            return self.matches_content(content)
        except GithubException as e:
            message = f"Error reading content from {result.repository.full_name}/{result.path}: {e.data['message']}"
            raise FilterException(self, message) from e

    def matches_content(self, content: str) -> bool:
        raise NotImplementedError


class ContentFilter(DecodedContentFilter):
    def __init__(self, content_filter: str):
        self.content_filter = content_filter

    def matches_content(self, content: str) -> bool:
        return self.content_filter in content


class RegexContentFilter(DecodedContentFilter):
    def __init__(self, content_filter: str):
        try:
            self.content_filter_pattern = re.compile(content_filter)
        except re.error as e:
            message = f"Failed to compile regular expression from '{content_filter}': {e}"
            raise FilterException(self, message) from e

    def matches_content(self, content: str) -> bool:
        return bool(self.content_filter_pattern.search(content))


class NotArchivedFilter(Filter):
    def __init__(self):
        self.cache = {}

    def __call__(self, result: ContentFile) -> bool:
        if result.repository.full_name not in self.cache:
            self.cache[result.repository.full_name] = not result.repository.archived
        return self.cache[result.repository.full_name]


class PathFilter(Filter):
    def __init__(self, path_filter: str):
        self.uses_core_api = False
        self.path_filter = path_filter

    def __call__(self, result: ContentFile) -> bool:
        return self.path_filter in result.path
