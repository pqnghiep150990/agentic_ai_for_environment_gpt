from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class AssessmentRequest:
    site_id: str
    timestamp: datetime
    sensor_data: Dict[str, Any]
    task: str = "environmental_assessment"


@dataclass
class AssessmentContext:
    request: AssessmentRequest
    normalized_data: Dict[str, float] = field(default_factory=dict)
    ingestion_metadata: Dict[str, Any] = field(default_factory=dict)
    retrieval_chunks: List[str] = field(default_factory=list)
    reasoning: Dict[str, Any] = field(default_factory=dict)
    tool_outputs: Dict[str, float] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    evaluation: Dict[str, float] = field(default_factory=dict)
    reliability: Dict[str, float] = field(default_factory=dict)
    governance: Dict[str, Any] = field(default_factory=dict)
    report: Dict[str, Any] = field(default_factory=dict)
