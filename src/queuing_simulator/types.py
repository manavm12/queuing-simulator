from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

JobId = int
Discipline = Literal["fifo", "sjf"]
Admission = Literal["always", "cap"]


@dataclass
class Job:
    id: JobId
    arrival_t: int
    service_time: int
    patience: int

    start_t: int | None = None
    end_t: int | None = None


@dataclass
class QueueState:
    t: int
    waiting: list[Job]

    in_service: Job | None
    remaining: int  # remaining service time for in_service (0 if none)

    completed: list[Job]
    dropped: list[Job]

    # bookkeeping
    arrived_count: int = 0
    dropped_count: int = 0
    completed_count: int = 0


@dataclass(frozen=True)
class StepEvent:
    """
    What happened at a single timestep (for metrics + debugging).
    """
    t: int
    arrivals: int
    admitted: int
    dropped: int
    started_job_id: JobId | None
    completed_job_id: JobId | None
    queue_len: int
    server_busy: bool
