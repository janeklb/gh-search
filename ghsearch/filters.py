from github.ContentFile import ContentFile


class Filter:
    """This filter uses the core api"""

    uses_core_api = True

    def __call__(self, result: ContentFile) -> bool:
        raise NotImplementedError


class ContentFilter(Filter):
    def __init__(self, content_filter: str):
        self.content_filter = content_filter

    def __call__(self, result: ContentFile) -> bool:
        return self.content_filter in result.decoded_content.decode("utf-8")


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
