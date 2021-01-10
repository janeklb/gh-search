import os
from typing import Any, Dict

from github import Github


def build_client() -> Github:
    client_params: Dict[str, Any] = {"per_page": 1000}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        client_params["login_or_token"] = token
    base_url = os.getenv("GITHUB_API_URL")
    if base_url:
        client_params["base_url"] = base_url
    return Github(**client_params)
