from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from integrations.notion_client import (
    extract_rich_text,
    extract_select,
    extract_title,
)


@dataclass
class IncidentRecord:
    page_id: str
    service_name: str
    error_logs: str
    severity: str


@dataclass
class PropertyMapping:
    service_name: str
    error_logs: str
    severity: str


def parse_incident(page: Dict, property_mapping: PropertyMapping) -> IncidentRecord:
    properties = page.get("properties", {})

    service_name = extract_title(properties, property_mapping.service_name)
    if not service_name:
        service_name = "unknown-service"

    error_logs = extract_rich_text(properties, property_mapping.error_logs)
    if not error_logs:
        error_logs = "No logs provided."

    severity = extract_select(properties, property_mapping.severity)
    if not severity:
        severity = "medium"

    return IncidentRecord(
        page_id=page["id"],
        service_name=service_name,
        error_logs=error_logs,
        severity=severity,
    )
