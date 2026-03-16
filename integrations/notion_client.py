from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class NotionConfig:
    api_key: str
    database_id: str


class NotionClient:
    def __init__(self, config: NotionConfig) -> None:
        self.config = config
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def query_incidents(self, target_status: Optional[str], status_property_name: str) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"page_size": 50}
        if target_status:
            payload["filter"] = {
                "property": status_property_name,
                "status": {"equals": target_status},
            }

        response = requests.post(
            f"{self.base_url}/databases/{self.config.database_id}/query",
            headers=self.headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

    def update_page(self, page_id: str, properties: Dict[str, Any]) -> None:
        response = requests.patch(
            f"{self.base_url}/pages/{page_id}",
            headers=self.headers,
            json={"properties": properties},
            timeout=30,
        )
        response.raise_for_status()

    def append_comment(self, page_id: str, message: str) -> None:
        response = requests.post(
            f"{self.base_url}/comments",
            headers=self.headers,
            json={
                "parent": {"page_id": page_id},
                "rich_text": [{"type": "text", "text": {"content": message}}],
            },
            timeout=30,
        )
        response.raise_for_status()


def rich_text_property(value: str) -> Dict[str, Any]:
    return {
        "rich_text": [
            {
                "type": "text",
                "text": {
                    "content": value[:2000],
                },
            }
        ]
    }


def status_property(value: str) -> Dict[str, Any]:
    return {"status": {"name": value}}


def select_property(value: str) -> Dict[str, Any]:
    return {"select": {"name": value}}


def extract_title(properties: Dict[str, Any], property_name: str) -> str:
    entry = properties.get(property_name, {})
    chunks = entry.get("title", [])
    return " ".join(chunk.get("plain_text", "") for chunk in chunks).strip()


def extract_rich_text(properties: Dict[str, Any], property_name: str) -> str:
    entry = properties.get(property_name, {})
    chunks = entry.get("rich_text", [])
    return " ".join(chunk.get("plain_text", "") for chunk in chunks).strip()


def extract_status(properties: Dict[str, Any], property_name: str) -> str:
    entry = properties.get(property_name, {})
    status_entry = entry.get("status")
    if isinstance(status_entry, dict):
        return status_entry.get("name", "")
    return ""


def extract_select(properties: Dict[str, Any], property_name: str) -> str:
    entry = properties.get(property_name, {})
    select_entry = entry.get("select")
    if isinstance(select_entry, dict):
        return select_entry.get("name", "")
    return ""
