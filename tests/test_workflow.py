from datetime import datetime

import pytest

from agentic_env_ai.agents import DataIngestionAgent
from agentic_env_ai.demo import run_demo
from agentic_env_ai.models import AssessmentContext, AssessmentRequest


def test_demo_report_has_required_sections():
    report = run_demo()
    assert "summary" in report
    assert "ingestion" in report
    assert "evaluation" in report
    assert "reliability" in report
    assert "governance" in report


def test_data_ingestion_supports_alias_and_conversion():
    agent = DataIngestionAgent()
    req = AssessmentRequest(
        site_id="S-1",
        timestamp=datetime.utcnow(),
        sensor_data={
            "pm2_5": 12,
            "pm10": 20,
            "no2_ppb": 10,
            "water_ph": 7.2,
            "temp_c": 25,
        },
    )
    ctx = agent.run(AssessmentContext(request=req))
    assert ctx.normalized_data["no2"] == 18.8
    assert ctx.ingestion_metadata["status"] == "pass"


def test_data_ingestion_rejects_missing_required_sensor():
    agent = DataIngestionAgent()
    req = AssessmentRequest(
        site_id="S-2",
        timestamp=datetime.utcnow(),
        sensor_data={"pm25": 12, "pm10": 30, "no2": 20, "ph": 7.1},
    )
    with pytest.raises(ValueError, match="Missing required sensor: temperature_c"):
        agent.run(AssessmentContext(request=req))


def test_data_ingestion_adds_warning_for_operating_range_breach():
    agent = DataIngestionAgent()
    req = AssessmentRequest(
        site_id="S-3",
        timestamp=datetime.utcnow(),
        sensor_data={
            "pm25": 80,
            "pm10": 20,
            "no2": 10,
            "ph": 7,
            "temperature_c": 25,
        },
    )
    ctx = agent.run(AssessmentContext(request=req))
    assert ctx.ingestion_metadata["status"] == "pass_with_warnings"
    assert ctx.ingestion_metadata["quality_score"] < 1.0
