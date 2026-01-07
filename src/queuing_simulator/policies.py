from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from policy_eval.abstractions.policy import Policy, PolicyContext
from .types import Discipline, Admission


@dataclass(frozen=True)
class QueuePolicyAction:
    """
    What the policy decides at a timestep.
    """

    discipline: Discipline
    capacity: int | None = None  # only used if admission == "cap"


class FIFOPolicy:
    """
    First-In-First-Out service.
    """
    name = "fifo"

    def __init__(self, capacity: int | None = None):
        self.capacity = capacity
        self.admission: Admission = "cap" if capacity is not None else "always"

    def decide(self, ctx: PolicyContext) -> QueuePolicyAction:
        return QueuePolicyAction(
            admission=self.admission,
            discipline="fifo",
            capacity=self.capacity,
        )


class SJFPolicy:
    """
    Shortest-Job-First service.
    Assumes service_time is visible to the policy.
    """
    name = "sjf"

    def __init__(self, capacity: int | None = None):
        self.capacity = capacity
        self.admission: Admission = "cap" if capacity is not None else "always"

    def decide(self, ctx: PolicyContext) -> QueuePolicyAction:
        return QueuePolicyAction(
            admission=self.admission,
            discipline="sjf",
            capacity=self.capacity,
        )
