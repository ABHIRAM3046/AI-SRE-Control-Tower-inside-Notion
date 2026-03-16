from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import requests


@dataclass
class GitHubDispatchConfig:
    owner: str
    repo: str
    workflow_file: str
    ref: str
    token: str


class GitHubActionsClient:
    def __init__(self, config: GitHubDispatchConfig) -> None:
        self.config = config

    def trigger_workflow(self, inputs: Optional[Dict[str, str]] = None) -> str:
        endpoint = (
            f"https://api.github.com/repos/{self.config.owner}/{self.config.repo}/"
            f"actions/workflows/{self.config.workflow_file}/dispatches"
        )

        payload = {
            "ref": self.config.ref,
            "inputs": inputs or {},
        }

        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json=payload,
            timeout=30,
        )

        if response.status_code in {200, 201, 204}:
            return "GitHub Actions workflow dispatched successfully."

        return f"GitHub Actions dispatch failed: {response.status_code} {response.text}"
