from __future__ import annotations

from typing import Any

from policy_eval.abstractions.actor import Observation
from policy_eval.abstractions.policy import PolicyContext
from policy_eval.core.types import Event, Trajectory

from .actors import ArrivalActor, ArrivalParams
from .policies import QueuePolicyAction
from .types import Job, QueueState, StepEvent


class SingleQueueDomain:
    """
    Single queue, single server, discrete-time, non-preemptive.
    - Actor generates arrivals + job traits.
    - Policy controls admission (always/cap) and discipline (fifo/sjf).
    - Reneging happens when waited time > patience.
    """
    name = "single_queue_v1"

    def __init__(self, arrival_params: ArrivalParams):
        self.arrivals = ArrivalActor(arrival_params)

    # ---------- Framework hooks ----------

    def initial_state(self, rng: Any) -> QueueState:
        return QueueState(
            t=0,
            waiting=[],
            in_service=None,
            remaining=0,
            completed=[],
            dropped=[],
            arrived_count=0,
            dropped_count=0,
            completed_count=0,
        )

    def actors(self, state: QueueState):
        return [self.arrivals]

    def policy_context(self, state: QueueState, t: int) -> PolicyContext:
        # Policy sees system-level view only (no patience).
        return PolicyContext(
            t=t,
            system_view={
                "queue_len": len(state.waiting),
                "server_busy": state.in_service is not None,
            },
        )

    def observe(self, state: QueueState, actor: ArrivalActor, t: int) -> Observation:
        # Actor sees only what we allow. No policy info.
        return Observation(t=t, data={"queue_len": len(state.waiting)})

    def transition(
        self,
        state: QueueState,
        policy_action: QueuePolicyAction,
        actor_actions: list[Any],
        rng: Any,
        t: int,
    ) -> QueueState:
        # We mutate the state object (fine for v1, but keep it disciplined).
        state.t = t

        arrivals = 0
        admitted = 0
        dropped = 0
        started_job_id = None
        completed_job_id = None

        # 0) Reneging: drop any waiting jobs that exceeded patience
        # waited = t - arrival_t
        still_waiting: list[Job] = []
        for job in state.waiting:
            waited = t - job.arrival_t
            if waited > job.patience:
                dropped += 1
                state.dropped.append(job)
            else:
                still_waiting.append(job)
        state.waiting = still_waiting

        # 1) Apply actor arrival result (0 or 1 arrival in v1)
        a = actor_actions[0]
        if a.get("arrived"):
            arrivals = 1
            state.arrived_count += 1

            if a.get("balked"):
                dropped += 1
                state.dropped_count += 1
            else:
                job: Job = a["job"]

                # Admission policy
                allow = True
                if policy_action.admission == "cap":
                    cap = policy_action.capacity
                    if cap is None:
                        raise ValueError("cap admission requires capacity")
                    if len(state.waiting) >= cap:
                        allow = False

                if allow:
                    admitted = 1
                    state.waiting.append(job)
                else:
                    dropped += 1
                    state.dropped.append(job)

        # 2) Service progression: advance current job (if any)
        if state.in_service is not None:
            state.remaining -= 1
            if state.remaining <= 0:
                # complete
                state.in_service.end_t = t
                state.completed.append(state.in_service)
                state.completed_count += 1
                completed_job_id = state.in_service.id
                state.in_service = None
                state.remaining = 0

        # 3) If idle, start next job based on discipline
        if state.in_service is None and state.waiting:
            idx = self._select_next_index(state.waiting, policy_action.discipline)
            job = state.waiting.pop(idx)
            job.start_t = t
            state.in_service = job
            state.remaining = job.service_time
            started_job_id = job.id

        # 4) Record step event into state for record()
        state._last_event = StepEvent(  # type: ignore[attr-defined]
            t=t,
            arrivals=arrivals,
            admitted=admitted,
            dropped=dropped,
            started_job_id=started_job_id,
            completed_job_id=completed_job_id,
            queue_len=len(state.waiting),
            server_busy=(state.in_service is not None),
        )

        return state

    def record(self, state: QueueState, t: int) -> Event:
        ev: StepEvent = state._last_event  # type: ignore[attr-defined]
        return Event(t=t, payload=ev)

    def finalize(self, events: list[Event], final_state: QueueState) -> Trajectory:
        return Trajectory(events=tuple(events), final_state=final_state)

    # ---------- Helpers ----------

    @staticmethod
    def _select_next_index(waiting: list[Job], discipline: str) -> int:
        if discipline == "fifo":
            return 0
        if discipline == "sjf":
            # shortest service time first
            return min(range(len(waiting)), key=lambda i: waiting[i].service_time)
        raise ValueError(f"Unknown discipline: {discipline}")
