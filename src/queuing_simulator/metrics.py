from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from policy_eval.core.types import Trajectory

from .types import QueueState, Job


def _completed_jobs(traj: Trajectory) -> list[Job]:
    s: QueueState = traj.final_state
    return list(s.completed)


def _wait_times(traj: Trajectory) -> list[int]:
    waits: list[int] = []
    for job in _completed_jobs(traj):
        if job.start_t is None:
            continue  # should not happen for completed jobs
        waits.append(int(job.start_t - job.arrival_t))
    return waits


def _quantile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])

    pos = (len(sorted_vals) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return float(sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac)


@dataclass(frozen=True)
class AvgWaitTimeMetric:
    name: str = "avg_wait_time"

    def evaluate(self, traj: Trajectory) -> float:
        waits = _wait_times(traj)
        if not waits:
            return 0.0
        return float(sum(waits) / len(waits))


@dataclass(frozen=True)
class TotalWaitTimeMetric:
    name: str = "total_wait_time"

    def evaluate(self, traj: Trajectory) -> float:
        waits = _wait_times(traj)
        return float(sum(waits))


@dataclass(frozen=True)
class P90WaitTimeMetric:
    name: str = "p90_wait_time"

    def evaluate(self, traj: Trajectory) -> float:
        waits = sorted(float(w) for w in _wait_times(traj))
        return _quantile(waits, 0.90)


@dataclass(frozen=True)
class ThroughputMetric:
    name: str = "throughput"

    def evaluate(self, traj: Trajectory) -> float:
        s: QueueState = traj.final_state
        return float(len(s.completed))


@dataclass(frozen=True)
class DropRateMetric:
    """
    dropped / arrived
    Includes:
    - balking at arrival (actor chose not to join)
    - rejection due to cap
    - reneging after waiting too long
    """
    name: str = "drop_rate"

    def evaluate(self, traj: Trajectory) -> float:
        s: QueueState = traj.final_state
        arrived = float(s.arrived_count)
        if arrived <= 0:
            return 0.0
        return float(len(s.dropped)) / arrived


@dataclass(frozen=True)
class UtilizationMetric:
    """
    Fraction of timesteps where server was busy (in_service != None).
    Computed from event log.
    """
    name: str = "utilization"

    def evaluate(self, traj: Trajectory) -> float:
        if not traj.events:
            return 0.0
        busy = 0
        for e in traj.events:
            ev = e.payload
            # ev is StepEvent; payload stored as object
            if getattr(ev, "server_busy", False):
                busy += 1
        return float(busy) / float(len(traj.events))
