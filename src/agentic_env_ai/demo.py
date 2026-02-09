from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import AssessmentRequest
from .orchestrator import Orchestrator

MOCK_CORPUS = {
    "pm25": "WHO PM2.5 guideline: annual mean under 5 µg/m3 where feasible.",
    "no2": "WHO NO2 guideline: annual average under 10 µg/m3.",
    "ph": "Surface water pH is typically acceptable in range 6.5-8.5.",
}


def run_demo() -> dict:
    orchestrator = Orchestrator(corpus=MOCK_CORPUS)
    request = AssessmentRequest(
        site_id="SITE-001",
        timestamp=datetime.utcnow(),
        sensor_data={
            "pm25": 38,
            "pm10": 62,
            "no2": 17,
            "ph": 7.3,
            "temperature_c": 31.2,
        },
    )
    context = orchestrator.run(request)
    return context.report


def save_outputs(root: Path) -> None:
    report = run_demo()
    root.mkdir(parents=True, exist_ok=True)
    (root / "environmental_assessment_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    save_outputs(Path("reports"))
