from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .demo import MOCK_CORPUS
from .models import AssessmentRequest
from .orchestrator import Orchestrator


def run_stress_scenarios() -> list[dict]:
    orchestrator = Orchestrator(corpus=MOCK_CORPUS)
    scenarios = [
        {"site_id": "SITE-001", "pm25": 25, "pm10": 40, "no2": 12, "ph": 7.1, "temperature_c": 27},
        {"site_id": "SITE-002", "pm25": 58, "pm10": 90, "no2": 31, "ph": 5.9, "temperature_c": 32},
        {"site_id": "SITE-003", "pm25": 15, "pm10": 29, "no2": 8, "ph": 8.8, "temperature_c": 24},
    ]
    outputs = []
    for s in scenarios:
        req = AssessmentRequest(site_id=s["site_id"], timestamp=datetime.utcnow(), sensor_data=s)
        context = orchestrator.run(req)
        outputs.append(
            {
                "site_id": s["site_id"],
                "reliability": context.reliability,
                "evaluation": context.evaluation,
                "governance": context.governance,
            }
        )
    return outputs


def save_log(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run_stress_scenarios(), indent=2), encoding="utf-8")


if __name__ == "__main__":
    save_log(Path("logs/evaluation_monitoring_log.json"))
