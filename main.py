from __future__ import annotations

import argparse
import os
import time
from typing import List

from dotenv import load_dotenv

from agent.ai_analyzer import AIAnalyzer
from agent.incident_handler import HandlerPropertyMapping, IncidentHandler
from integrations.github_actions import GitHubActionsClient, GitHubDispatchConfig
from integrations.kubernetes import KubernetesClient, KubernetesConfig
from integrations.notion_client import NotionClient, NotionConfig
from workflows.auto_fix import AutoFixExecutor, AutomationConfig
from workflows.incident_detection import PropertyMapping, parse_incident


def bool_from_env(name: str, default: str = "false") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def build_notion_client() -> NotionClient:
    api_key = os.getenv("NOTION_API_KEY", "").strip()
    database_id = os.getenv("NOTION_DATABASE_ID", "").strip()
    if not api_key or not database_id:
        raise ValueError("NOTION_API_KEY and NOTION_DATABASE_ID are required.")
    return NotionClient(NotionConfig(api_key=api_key, database_id=database_id))


def build_automation() -> AutoFixExecutor:
    automation_config = AutomationConfig(
        enabled=bool_from_env("AUTOMATION_ENABLED", "true"),
        backend=os.getenv("AUTOMATION_BACKEND", "none"),
    )

    github_client = None
    if automation_config.backend.lower().strip() == "github":
        owner = os.getenv("GITHUB_OWNER", "").strip()
        repository = os.getenv("GITHUB_REPO", "").strip()
        workflow_file = os.getenv("GITHUB_WORKFLOW_FILE", "").strip()
        reference = os.getenv("GITHUB_REF", "main").strip()
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if all([owner, repository, workflow_file, token]):
            github_client = GitHubActionsClient(
                GitHubDispatchConfig(
                    owner=owner,
                    repo=repository,
                    workflow_file=workflow_file,
                    ref=reference,
                    token=token,
                )
            )

    kubernetes_client = None
    if automation_config.backend.lower().strip() == "kubernetes":
        namespace = os.getenv("KUBE_NAMESPACE", "default").strip()
        deployment_prefix = os.getenv("KUBE_DEPLOYMENT_PREFIX", "").strip()
        kubernetes_client = KubernetesClient(
            KubernetesConfig(namespace=namespace, deployment_prefix=deployment_prefix)
        )

    return AutoFixExecutor(
        config=automation_config,
        github_client=github_client,
        kubernetes_client=kubernetes_client,
    )


def build_handler(notion_client: NotionClient) -> IncidentHandler:
    analyzer = AIAnalyzer(
        provider=os.getenv("AI_PROVIDER", "openai"),
        api_key=os.getenv("OPENAI_API_KEY", "").strip() or None,
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
    )

    auto_fix_executor = build_automation()

    mapping = HandlerPropertyMapping(
        error_logs=os.getenv("NOTION_PROP_ERROR_LOGS", "Error Logs"),
        severity=os.getenv("NOTION_PROP_SEVERITY", "Severity"),
        ai_analysis=os.getenv("NOTION_PROP_AI_ANALYSIS", "AI Analysis"),
        recommended_fix=os.getenv("NOTION_PROP_RECOMMENDED_FIX", "Recommended Fix"),
        deployment_trigger=os.getenv("NOTION_PROP_DEPLOYMENT_TRIGGER", "Deployment Trigger"),
        incident_summary=os.getenv("NOTION_PROP_INCIDENT_SUMMARY", "Incident Summary"),
        status=os.getenv("NOTION_PROP_STATUS", "Status"),
        status_type=os.getenv("NOTION_PROP_STATUS_TYPE", "select"),
        deployment_trigger_type=os.getenv("NOTION_PROP_DEPLOYMENT_TRIGGER_TYPE", "checkbox"),
    )

    return IncidentHandler(
        notion_client=notion_client,
        analyzer=analyzer,
        auto_fix_executor=auto_fix_executor,
        mapping=mapping,
    )


def process_once() -> List[dict]:
    notion_client = build_notion_client()
    incident_handler = build_handler(notion_client)

    incident_mapping = PropertyMapping(
        service_name=os.getenv("NOTION_PROP_SERVICE_NAME", "Service Name"),
        error_logs=os.getenv("NOTION_PROP_ERROR_LOGS", "Error Logs"),
        severity=os.getenv("NOTION_PROP_SEVERITY", "Severity"),
    )

    target_status = os.getenv("NOTION_TARGET_STATUS", "Open").strip()
    status_property_name = os.getenv("NOTION_PROP_STATUS", "Status").strip()
    status_property_type = os.getenv("NOTION_PROP_STATUS_TYPE", "select").strip()
    pages = notion_client.query_incidents(
        target_status=target_status if target_status else None,
        status_property_name=status_property_name,
        status_property_type=status_property_type,
    )

    results: List[dict] = []
    for page in pages:
        incident = parse_incident(page=page, property_mapping=incident_mapping)
        result = incident_handler.process(incident)
        results.append(result)
        print(f"Processed incident: {result}")

    if not pages:
        print("No incidents matched the current filter.")

    return results


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="AI SRE Control Tower incident processor")
    parser.add_argument(
        "--poll",
        action="store_true",
        help="Continuously poll Notion incidents based on POLL_SECONDS.",
    )
    args = parser.parse_args()

    if args.poll:
        poll_seconds = int(os.getenv("POLL_SECONDS", "30"))
        while True:
            try:
                process_once()
            except Exception as error:
                print(f"Run failed: {error}")
            time.sleep(poll_seconds)
        
    process_once()


if __name__ == "__main__":
    main()
