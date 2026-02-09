from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, List, Tuple

from .models import AssessmentContext


class BaseAgent:
    name = "base"

    def run(self, context: AssessmentContext) -> AssessmentContext:
        raise NotImplementedError


@dataclass(frozen=True)
class SensorSpec:
    canonical_name: str
    aliases: Tuple[str, ...]
    min_value: float
    max_value: float
    hard_min: float
    hard_max: float
    unit: str


class DataIngestionAgent(BaseAgent):
    """Validate, normalize, and quality-score sensor payloads."""

    name = "data_ingestion"

    SPECS: Dict[str, SensorSpec] = {
        "pm25": SensorSpec("pm25", ("pm2_5", "pm2.5", "pm25_ugm3"), 0.0, 55.0, 0.0, 1000.0, "ug/m3"),
        "pm10": SensorSpec("pm10", ("pm10_ugm3",), 0.0, 150.0, 0.0, 1200.0, "ug/m3"),
        "no2": SensorSpec("no2", ("no2_ppb", "nitrogen_dioxide"), 0.0, 200.0, 0.0, 2000.0, "ug/m3"),
        "ph": SensorSpec("ph", ("water_ph",), 6.5, 8.5, 0.0, 14.0, "pH"),
        "temperature_c": SensorSpec("temperature_c", ("temp_c", "temperature"), -10.0, 45.0, -50.0, 80.0, "celsius"),
    }

    NO2_PPB_TO_UGM3 = 1.88

    def _resolve_value(self, payload: Dict[str, object], spec: SensorSpec) -> tuple[str, float]:
        for key in (spec.canonical_name, *spec.aliases):
            if key in payload:
                raw = payload[key]
                try:
                    return key, float(raw)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Sensor '{key}' is not numeric: {raw!r}") from exc
        raise ValueError(f"Missing required sensor: {spec.canonical_name}")

    def _normalize(self, key: str, canonical_name: str, value: float) -> tuple[float, str]:
        if canonical_name == "no2" and key == "no2_ppb":
            return value * self.NO2_PPB_TO_UGM3, "Converted no2_ppb to ug/m3"
        return value, "No unit conversion"

    def run(self, context: AssessmentContext) -> AssessmentContext:
        payload = context.request.sensor_data
        normalized: Dict[str, float] = {}
        conversion_notes: List[str] = []
        warnings: List[str] = []
        quality_issues = 0

        for canonical_name, spec in self.SPECS.items():
            source_key, source_value = self._resolve_value(payload, spec)
            value, note = self._normalize(source_key, canonical_name, source_value)
            conversion_notes.append(f"{canonical_name}: {note}")

            if not (spec.hard_min <= value <= spec.hard_max):
                raise ValueError(
                    f"Sensor '{canonical_name}' has physically impossible value: {value} {spec.unit}"
                )

            if not (spec.min_value <= value <= spec.max_value):
                warnings.append(
                    f"{canonical_name}={value} {spec.unit} outside recommended operating range "
                    f"[{spec.min_value}, {spec.max_value}]"
                )
                quality_issues += 1

            normalized[canonical_name] = round(value, 4)

        quality_score = round(max(0.0, 1.0 - (quality_issues / len(self.SPECS))), 4)
        context.normalized_data = normalized
        context.ingestion_metadata = {
            "source_field_count": len(payload),
            "required_sensor_count": len(self.SPECS),
            "conversion_notes": conversion_notes,
            "warnings": warnings,
            "quality_score": quality_score,
            "status": "pass" if not warnings else "pass_with_warnings",
        }
        return context


class RetrievalAgent(BaseAgent):
    name = "retrieval"

    def __init__(self, corpus: Dict[str, str]) -> None:
        self.corpus = corpus

    def run(self, context: AssessmentContext) -> AssessmentContext:
        query_terms = ["pm25", "no2", "ph"]
        chunks: List[str] = []
        for key in query_terms:
            if key in self.corpus:
                chunks.append(self.corpus[key])
        context.retrieval_chunks = chunks
        return context


class ReasoningAgent(BaseAgent):
    name = "reasoning"

    def run(self, context: AssessmentContext) -> AssessmentContext:
        data = context.normalized_data
        air_score = 100 - min(100, (data["pm25"] * 1.2 + data["no2"] * 0.6))
        water_ok = 6.5 <= data["ph"] <= 8.5
        reasoning = {
            "air_quality_score": round(max(0.0, air_score), 2),
            "water_status": "normal" if water_ok else "attention",
            "explanation": "Combined particulate and NO2 loading with pH threshold checks.",
        }
        context.reasoning = reasoning
        return context


class ToolAgent(BaseAgent):
    name = "tool"

    def run(self, context: AssessmentContext) -> AssessmentContext:
        vals = list(context.normalized_data.values())
        context.tool_outputs = {
            "mean_sensor_value": round(mean(vals), 3),
            "max_sensor_value": round(max(vals), 3),
        }
        return context


class MemoryAgent(BaseAgent):
    name = "memory"

    def __init__(self) -> None:
        self._store: Dict[str, List[float]] = {}

    def run(self, context: AssessmentContext) -> AssessmentContext:
        site = context.request.site_id
        self._store.setdefault(site, []).append(context.reasoning["air_quality_score"])
        history = self._store[site]
        context.memory = {
            "historical_count": len(history),
            "historical_air_quality_mean": round(mean(history), 3),
        }
        return context


class EvaluationAgent(BaseAgent):
    name = "evaluation"

    def run(self, context: AssessmentContext) -> AssessmentContext:
        retrieval_accuracy = 1.0 if len(context.retrieval_chunks) >= 3 else 0.6
        reasoning_consistency = 1.0 if "explanation" in context.reasoning else 0.5
        tool_correctness = (
            1.0 if context.tool_outputs["max_sensor_value"] >= context.tool_outputs["mean_sensor_value"] else 0.0
        )
        ece = abs((context.reasoning["air_quality_score"] / 100) - retrieval_accuracy) * 0.1
        context.evaluation = {
            "retrieval_accuracy": round(retrieval_accuracy, 3),
            "reasoning_consistency": round(reasoning_consistency, 3),
            "tool_correctness": round(tool_correctness, 3),
            "ece": round(ece, 4),
        }
        return context


class ReliabilityMonitor(BaseAgent):
    name = "reliability"

    def run(self, context: AssessmentContext) -> AssessmentContext:
        e = context.evaluation
        reliability = (
            0.3 * e["retrieval_accuracy"]
            + 0.35 * e["reasoning_consistency"]
            + 0.25 * e["tool_correctness"]
            + 0.1 * (1 - e["ece"])
        )
        context.reliability = {
            "end_to_end": round(reliability, 4),
            "status": "high" if reliability >= 0.85 else "moderate" if reliability >= 0.7 else "low",
        }
        return context


class GovernanceAgent(BaseAgent):
    name = "governance"

    def run(self, context: AssessmentContext) -> AssessmentContext:
        alerts = []
        if context.normalized_data["pm25"] > 55:
            alerts.append("PM2.5 exceeds governance threshold")
        if context.normalized_data["ph"] < 6.0 or context.normalized_data["ph"] > 9.0:
            alerts.append("pH outside safe governance range")
        context.governance = {
            "alerts": alerts,
            "safe_to_publish": len(alerts) == 0,
        }
        return context
