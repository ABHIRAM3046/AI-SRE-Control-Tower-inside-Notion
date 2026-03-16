from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from integrations.github_actions import GitHubActionsClient
from integrations.kubernetes import KubernetesClient


@dataclass
class AutomationConfig:
    enabled: bool
    backend: str


class AutoFixExecutor:
    def __init__(
        self,
        config: AutomationConfig,
        github_client: Optional[GitHubActionsClient],
        kubernetes_client: Optional[KubernetesClient],
    ) -> None:
        self.config = config
        self.github_client = github_client
        self.kubernetes_client = kubernetes_client

    def maybe_execute(self, service_name: str, recommended_fix: str, severity: str) -> str:
        if not self.config.enabled:
            return "Automation disabled."

        normalized_severity = severity.lower().strip()
        if normalized_severity not in {"high", "critical", "sev1", "sev2"}:
            return f"No automation executed for severity '{severity}'."

        backend = self.config.backend.lower().strip()
        if backend == "github":
            if self.github_client is None:
                return "GitHub backend selected but not configured."
            return self.github_client.trigger_workflow(
                inputs={
                    "service_name": service_name,
                    "recommended_fix": recommended_fix[:200],
                    "severity": severity,
                }
            )

        if backend == "kubernetes":
            if self.kubernetes_client is None:
                return "Kubernetes backend selected but not configured."
            return self.kubernetes_client.rollout_restart(service_name=service_name)

        return "No automation backend configured."
