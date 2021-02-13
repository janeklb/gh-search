from github.ContentFile import ContentFile


class Filter:
    def __call__(self, result: ContentFile) -> bool:
        raise NotImplementedError


class ContentFilter(Filter):
    def __init__(self, content_filter: str):
        self.content_filter = content_filter

    def __call__(self, result: ContentFile) -> bool:
        return self.content_filter in result.decoded_content.decode("utf-8")


class NotArchivedFilter(Filter):
    def __call__(self, result: ContentFile) -> bool:
        return not result.repository.archived


class PathFilter(Filter):
    def __init__(self, path_filter: str):
        self.path_filter = path_filter

    def __call__(self, result: ContentFile) -> bool:
        return self.path_filter in result.path
