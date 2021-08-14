from typing import Any, Dict

from github import Github

RESULTS_PER_PAGE = 100  # this is the max - see https://docs.github.com/en/rest/reference/search#search-code--parameters


def build_client(token: str, base_url: str = None) -> Github:
    client_params: Dict[str, Any] = {"per_page": RESULTS_PER_PAGE, "login_or_token": token}
    if base_url:
        client_params["base_url"] = base_url
    return Github(**client_params)
