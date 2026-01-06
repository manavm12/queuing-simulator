# Queuing Simulator – Domain Design (v1)

## Goal
Evaluate and compare queue policies under human uncertainty.

## Assumptions (v1)
- Single queue
- Single server
- Discrete time steps (t = 0,1,2,...)
- Service is non-preemptive (once a job starts, it finishes)
- Policy does NOT see human traits (e.g., patience)
- Metrics are computed from trajectory only (no feedback)

## Entities

### Job (unit of work)
Represents one customer/request after it enters the system.

Minimum fields:
- id
- arrival_t
- service_time
- patience (how long they will wait before leaving)
- start_t (set when service begins)
- end_t (set when service completes)

### State (world state)
Minimum:
- t
- waiting: list[Job]
- in_service: Job | None
- remaining_service: int
- completed: list[Job]
- dropped: list[Job]  (balked or reneged)

## Actors (humans)

### Arrival/Customer generator (v1: population actor)
Generates new customers (jobs) + their traits.

Observes:
- queue length (optional: estimated wait)

Outputs per timestep:
- 0 or 1 arrival (v1)  [later: multiple arrivals]
- if arrival occurs:
  - service_time sampled from distribution
  - patience sampled from distribution
  - (optional) balk decision based on queue length

Human behavior we model in v1:
- heterogeneity: different patience, different service time
- balking: refuse to join if queue looks too long (optional)
- reneging: leave after waiting > patience (recommended)

## Policies (system rules)

A policy makes TWO decisions:

### 1) Admission (who is allowed to join)
- always_admit
- cap_K (reject if len(waiting) >= K)

### 2) Service discipline (who gets served next)
- FIFO
- SJF (shortest-job-first)  
service_time is visible to policy


Policy action schema (conceptual):
{ admission_rule, discipline }

## Metrics (evaluated after run)
- avg_wait_time = mean(start_t - arrival_t) over completed
- p90_wait_time
- total_wait_time = sum(start_t - arrival_t)
- throughput = #completed
- drop_rate = #dropped / #arrived
- utilization = fraction of time server busy

## Out of scope (v1)
- Multi-server
- Network of queues
- Strategic humans who react to policy
- Preemption (SRPT)
- Learning / optimization
