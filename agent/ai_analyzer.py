from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI


@dataclass
class AnalysisResult:
    possible_cause: str
    recommended_fix: str
    incident_summary: str


class AIAnalyzer:
    def __init__(
        self,
        provider: str,
        api_key: Optional[str],
        model: str,
    ) -> None:
        self.provider = provider.lower().strip()
        self.api_key = api_key
        self.model = model
        self.client: Optional[OpenAI] = None

        if self.provider == "openai" and self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def analyze_log(
        self,
        service_name: str,
        severity: str,
        error_logs: str,
    ) -> AnalysisResult:
        if self.client is None:
            return self._heuristic_analysis(service_name=service_name, severity=severity, error_logs=error_logs)

        prompt = self._build_prompt(service_name=service_name, severity=severity, error_logs=error_logs)
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=0.1,
        )

        text_output = response.output_text.strip()
        return self._parse_output(service_name=service_name, raw_output=text_output)

    def _build_prompt(self, service_name: str, severity: str, error_logs: str) -> str:
        return (
            "You are an SRE incident analyst. "
            "Given service name, severity, and raw logs, output strict JSON with keys: "
            "possible_cause, recommended_fix, incident_summary. "
            "Keep recommended_fix actionable and safe. "
            "Incident summary must be 1-2 lines for a status report.\n\n"
            f"Service: {service_name}\n"
            f"Severity: {severity}\n"
            f"Logs:\n{error_logs}\n"
        )

    def _parse_output(self, service_name: str, raw_output: str) -> AnalysisResult:
        try:
            payload = json.loads(raw_output)
            possible_cause = str(payload.get("possible_cause", "Unknown"))
            recommended_fix = str(payload.get("recommended_fix", "Investigate service health and recent changes."))
            incident_summary = str(payload.get("incident_summary", f"Incident detected in {service_name}."))
            return AnalysisResult(
                possible_cause=possible_cause,
                recommended_fix=recommended_fix,
                incident_summary=incident_summary,
            )
        except Exception:
            return AnalysisResult(
                possible_cause="AI output parsing failed.",
                recommended_fix="Review logs manually and validate dependent services.",
                incident_summary=f"Incident detected in {service_name}; manual review required.",
            )

    def _heuristic_analysis(self, service_name: str, severity: str, error_logs: str) -> AnalysisResult:
        lower_logs = error_logs.lower()

        if "503" in lower_logs and ("database" in lower_logs or "timeout" in lower_logs):
            return AnalysisResult(
                possible_cause="Database connection pool exhausted or database unreachable.",
                recommended_fix="Restart the service and increase DB pool size; check DB latency and connection limits.",
                incident_summary=(
                    f"{service_name} returned 503 errors due to database timeout symptoms. "
                    "Automated remediation is recommended."
                ),
            )

        if "oom" in lower_logs or "out of memory" in lower_logs:
            return AnalysisResult(
                possible_cause="Container or process memory limit exceeded.",
                recommended_fix="Scale memory limits and inspect memory leaks from recent releases.",
                incident_summary=f"{service_name} appears memory-constrained; scaling and profiling recommended.",
            )

        return AnalysisResult(
            possible_cause=f"General service degradation detected (severity={severity}).",
            recommended_fix="Restart impacted component, inspect recent deploys, and validate dependencies.",
            incident_summary=f"Incident detected in {service_name}; initial remediation steps have been suggested.",
        )
