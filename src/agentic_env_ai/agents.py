from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, List

from .models import AssessmentContext


class BaseAgent:
    name = "base"

    def run(self, context: AssessmentContext) -> AssessmentContext:
        raise NotImplementedError


class DataIngestionAgent(BaseAgent):
    name = "data_ingestion"
    REQUIRED = {"pm25", "pm10", "no2", "ph", "temperature_c"}

    def run(self, context: AssessmentContext) -> AssessmentContext:
        raw = context.request.sensor_data
        missing = self.REQUIRED - raw.keys()
        if missing:
            raise ValueError(f"Missing required sensors: {sorted(missing)}")

        normalized = {k: float(v) for k, v in raw.items() if k in self.REQUIRED}
        context.normalized_data = normalized
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
        tool_correctness = 1.0 if context.tool_outputs["max_sensor_value"] >= context.tool_outputs["mean_sensor_value"] else 0.0
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
