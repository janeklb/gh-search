from typing import Callable

from github.ContentFile import ContentFile


def build_content_filter(content_match: str) -> Callable[[ContentFile], bool]:
    def content_filter(result: ContentFile) -> bool:
        return content_match in result.decoded_content.decode("utf-8")

    return content_filter


def build_not_archived_filter() -> Callable[[ContentFile], bool]:
    def not_archived_filter(result: ContentFile) -> bool:
        return not result.repository.archived

    return not_archived_filter


def build_path_filter(path_match: str) -> Callable[[ContentFile], bool]:
    def path_filter(result: ContentFile) -> bool:
        return path_match in result.path

    return path_filter
