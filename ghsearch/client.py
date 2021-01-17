from typing import Any, Dict

from github import Github


def build_client(token: str, base_url: str = None) -> Github:
    client_params: Dict[str, Any] = {"per_page": 1000, "login_or_token": token}
    if base_url:
        client_params["base_url"] = base_url
    return Github(**client_params)
