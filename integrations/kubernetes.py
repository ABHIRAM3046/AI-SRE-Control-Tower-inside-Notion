from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class KubernetesConfig:
    namespace: str
    deployment_prefix: str


class KubernetesClient:
    def __init__(self, config: KubernetesConfig) -> None:
        self.config = config

    def rollout_restart(self, service_name: str) -> str:
        deployment_name = f"{self.config.deployment_prefix}{service_name}" if self.config.deployment_prefix else service_name

        command = [
            "kubectl",
            "rollout",
            "restart",
            f"deployment/{deployment_name}",
            "-n",
            self.config.namespace,
        ]

        process = subprocess.run(command, capture_output=True, text=True, check=False)
        if process.returncode == 0:
            return f"Kubernetes rollout restart triggered for {deployment_name}."

        stderr = process.stderr.strip() or process.stdout.strip()
        return f"Kubernetes rollout failed for {deployment_name}: {stderr}"
