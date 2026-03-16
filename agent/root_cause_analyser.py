from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Optional

from openai import OpenAI


@dataclass
class RootCauseResult:
    analysis: str
    fix: str
    timeline: str
    severity: str


def _build_prompt(service: str, error_log: str) -> str:
    return (
        "You are an SRE expert. Analyze the incident and return strict JSON only with keys: "
        "analysis, fix, timeline, severity. "
        "Severity must be one of: low, medium, high, critical. "
        "Keep timeline concise and practical.\n\n"
        f"Service: {service}\n"
        f"Error Log: {error_log}\n"
    )


def _heuristic_fallback(service: str, error_log: str) -> RootCauseResult:
    lowered = error_log.lower()

    if "503" in lowered and ("database" in lowered or "timeout" in lowered):
        return RootCauseResult(
            analysis="Database dependency timeout or connection pool exhaustion.",
            fix="Restart service, verify DB health, and increase connection pool limits if saturated.",
            timeline="Alert fired -> 503 errors observed -> dependency timeout identified -> restart and DB checks executed.",
            severity="high",
        )

    if "oom" in lowered or "memory" in lowered:
        return RootCauseResult(
            analysis="Service likely exceeded memory limits causing pod instability.",
            fix="Increase memory limits, inspect memory growth, and roll back recent memory-heavy changes if needed.",
            timeline="Error spike detected -> pod instability/OOM symptoms -> resource remediation applied.",
            severity="high",
        )

    return RootCauseResult(
        analysis="General service degradation with incomplete evidence for a single definitive cause.",
        fix="Inspect recent deployments, dependency health, and service logs; then restart impacted components.",
        timeline="Incident detected -> triage initiated -> remediation plan suggested for operator execution.",
        severity="medium",
    )


def analyze_incident_structured(service: str, error_log: str) -> RootCauseResult:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()

    if not api_key:
        return _heuristic_fallback(service=service, error_log=error_log)

    client: Optional[OpenAI] = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(
            model=model,
            input=_build_prompt(service=service, error_log=error_log),
            temperature=0.1,
        )
        content = response.output_text.strip()
        payload = json.loads(content)
        normalized_severity = str(payload.get("severity", "medium")).strip().lower()
        if normalized_severity not in {"low", "medium", "high", "critical"}:
            normalized_severity = "medium"
        return RootCauseResult(
            analysis=str(payload.get("analysis", "Unknown")),
            fix=str(payload.get("fix", "Investigate service dependencies and restart if required.")),
            timeline=str(payload.get("timeline", "Incident observed and triage initiated.")),
            severity=normalized_severity,
        )
    except Exception:
        return _heuristic_fallback(service=service, error_log=error_log)


def analyze_incident(service: str, error_log: str) -> str:
    result = analyze_incident_structured(service=service, error_log=error_log)
    return json.dumps(asdict(result))