from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from agent.ai_analyzer import AIAnalyzer
from integrations.notion_client import (
    NotionClient,
    checkbox_property,
    rich_text_property,
    select_property,
    status_property,
)
from workflows.auto_fix import AutoFixExecutor
from workflows.incident_detection import IncidentRecord


@dataclass
class HandlerPropertyMapping:
    error_logs: str
    severity: str
    ai_analysis: str
    recommended_fix: str
    deployment_trigger: str
    incident_summary: str
    status: str
    status_type: str
    deployment_trigger_type: str


class IncidentHandler:
    def __init__(
        self,
        notion_client: NotionClient,
        analyzer: AIAnalyzer,
        auto_fix_executor: AutoFixExecutor,
        mapping: HandlerPropertyMapping,
    ) -> None:
        self.notion_client = notion_client
        self.analyzer = analyzer
        self.auto_fix_executor = auto_fix_executor
        self.mapping = mapping

    def process(self, incident: IncidentRecord) -> Dict[str, str]:
        analysis = self.analyzer.analyze_log(
            service_name=incident.service_name,
            severity=incident.severity,
            error_logs=incident.error_logs,
        )

        automation_result = self.auto_fix_executor.maybe_execute(
            service_name=incident.service_name,
            recommended_fix=analysis.recommended_fix,
            severity=incident.severity,
            incident_page_id=incident.page_id,
        )

        normalized_status_type = self.mapping.status_type.strip().lower()
        if normalized_status_type == "select":
            status_update = select_property("In Progress")
        else:
            status_update = status_property("In Progress")

        normalized_trigger_type = self.mapping.deployment_trigger_type.strip().lower()
        if normalized_trigger_type == "checkbox":
            failed_markers = ["failed", "not configured", "disabled", "no automation executed"]
            automation_success = not any(marker in automation_result.lower() for marker in failed_markers)
            deployment_update = checkbox_property(automation_success)
        else:
            deployment_update = rich_text_property(automation_result)

        update_payload = {
            self.mapping.error_logs: rich_text_property(incident.error_logs),
            self.mapping.severity: select_property(incident.severity),
            self.mapping.ai_analysis: rich_text_property(f"Possible Cause: {analysis.possible_cause}"),
            self.mapping.recommended_fix: rich_text_property(analysis.recommended_fix),
            self.mapping.deployment_trigger: deployment_update,
            self.mapping.incident_summary: rich_text_property(analysis.incident_summary),
            self.mapping.status: status_update,
        }

        self.notion_client.update_page(page_id=incident.page_id, properties=update_payload)
        try:
            self.notion_client.append_comment(
                page_id=incident.page_id,
                message=(
                    f"AI Analysis complete for {incident.service_name}. "
                    f"Automation result: {automation_result}"
                ),
            )
        except Exception:
            pass

        return {
            "service": incident.service_name,
            "severity": incident.severity,
            "automation": automation_result,
        }
