from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from policy_eval.abstractions.actor import Observation

from .types import Job


@dataclass(frozen=True)
class ArrivalParams:
    """
    Population behavior parameters.
    """
    p_arrival: float                 # probability a customer arrives each timestep
    min_service: int                 # inclusive
    max_service: int                 # inclusive
    min_patience: int                # inclusive (timesteps)
    max_patience: int                # inclusive (timesteps)

    # Optional: balking based on queue length (set to 0.0 to disable)
    balk_per_customer: float = 0.0   # p_balk = min(1, balk_per_customer * queue_len)


class ArrivalActor:
    """
    A "population actor" that generates customer arrivals and assigns traits.
    It does NOT know the policy. It only sees the observation you give it.
    """
    id = "arrivals"

    def __init__(self, params: ArrivalParams):
        self.params = params
        self._next_id = 0

    def act(self, obs: Observation, rng: Any) -> dict[str, Any]:
        # Observation should be minimal. We'll assume it contains queue_len.
        queue_len = int(obs.data.get("queue_len", 0))

        # 1) Decide if someone arrives this timestep
        if rng.random() >= self.params.p_arrival:
            return {"arrived": False}

        # 2) Optional balking: decide if they refuse to join at the door
        p_balk = min(1.0, self.params.balk_per_customer * queue_len)
        if p_balk > 0.0 and (rng.random() < p_balk):
            return {"arrived": True, "balked": True}

        # 3) Sample job traits
        service_time = int(rng.integers(self.params.min_service, self.params.max_service + 1))
        patience = int(rng.integers(self.params.min_patience, self.params.max_patience + 1))

        job = Job(
            id=self._next_id,
            arrival_t=int(obs.t),
            service_time=service_time,
            patience=patience,
        )
        self._next_id += 1

        return {"arrived": True, "balked": False, "job": job}
