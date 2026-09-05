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
        except AssertionError as ae:
            message = f"Error reading content from {result.repository.full_name}/{result.path}: {str(ae)}"
            raise FilterException(self, message)

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


class PathFilter(Filter):
    uses_core_api = False

    def __init__(self, path_filter: str):
        try:
            self.path_filter_pattern = re.compile(path_filter)
        except re.error as e:
            message = f"Failed to compile path regular expression from '{path_filter}': {e}"
            raise FilterException(self, message) from e

    def __call__(self, result: ContentFile) -> bool:
        return bool(self.path_filter_pattern.search(result.path))
