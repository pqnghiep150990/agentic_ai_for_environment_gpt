from __future__ import annotations

from dataclasses import asdict
from typing import Dict

from .agents import (
    DataIngestionAgent,
    EvaluationAgent,
    GovernanceAgent,
    MemoryAgent,
    ReasoningAgent,
    ReliabilityMonitor,
    RetrievalAgent,
    ToolAgent,
)
from .models import AssessmentContext, AssessmentRequest


class Orchestrator:
    """Coordinates the 9-step environmental assessment workflow."""

    def __init__(self, corpus: Dict[str, str]) -> None:
        self.data_agent = DataIngestionAgent()
        self.retrieval_agent = RetrievalAgent(corpus)
        self.reasoning_agent = ReasoningAgent()
        self.tool_agent = ToolAgent()
        self.memory_agent = MemoryAgent()
        self.evaluation_agent = EvaluationAgent()
        self.reliability_monitor = ReliabilityMonitor()
        self.governance_agent = GovernanceAgent()

    def run(self, request: AssessmentRequest) -> AssessmentContext:
        context = AssessmentContext(request=request)

        # 1-2 Task framing + data ingestion
        context = self.data_agent.run(context)
        # 3 Retrieval
        context = self.retrieval_agent.run(context)
        # 4 Reasoning
        context = self.reasoning_agent.run(context)
        # 5 Tool execution
        context = self.tool_agent.run(context)
        # 6 Memory update
        context = self.memory_agent.run(context)
        # 7 Evaluation + reliability
        context = self.evaluation_agent.run(context)
        context = self.reliability_monitor.run(context)
        # 8 Governance checks
        context = self.governance_agent.run(context)
        # 9 Report
        context.report = {
            "site_id": request.site_id,
            "summary": context.reasoning,
            "ingestion": context.ingestion_metadata,
            "tool_outputs": context.tool_outputs,
            "evaluation": context.evaluation,
            "reliability": context.reliability,
            "governance": context.governance,
            "retrieval_evidence": context.retrieval_chunks,
        }
        return context

    @staticmethod
    def to_dict(context: AssessmentContext) -> Dict:
        return asdict(context)
