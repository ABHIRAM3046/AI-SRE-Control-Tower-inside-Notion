from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from agent.ai_analyzer import AIAnalyzer
from integrations.notion_client import NotionClient, rich_text_property, status_property
from workflows.auto_fix import AutoFixExecutor
from workflows.incident_detection import IncidentRecord


@dataclass
class HandlerPropertyMapping:
    ai_analysis: str
    recommended_fix: str
    deployment_trigger: str
    incident_summary: str
    status: str


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
        )

        update_payload = {
            self.mapping.ai_analysis: rich_text_property(f"Possible Cause: {analysis.possible_cause}"),
            self.mapping.recommended_fix: rich_text_property(analysis.recommended_fix),
            self.mapping.deployment_trigger: rich_text_property(automation_result),
            self.mapping.incident_summary: rich_text_property(analysis.incident_summary),
            self.mapping.status: status_property("In Progress"),
        }

        self.notion_client.update_page(page_id=incident.page_id, properties=update_payload)
        self.notion_client.append_comment(
            page_id=incident.page_id,
            message=(
                f"AI Analysis complete for {incident.service_name}. "
                f"Automation result: {automation_result}"
            ),
        )

        return {
            "service": incident.service_name,
            "severity": incident.severity,
            "automation": automation_result,
        }
