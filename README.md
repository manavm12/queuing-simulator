# Queuing Simulator (Policy Evaluation Domain)

A discrete-event queuing simulator built as a **domain module** for an existing Policy Evaluation Framework.

The goal is to model real-world queueing situations (e.g., single-server, multi-server, priorities, routing)
and evaluate different **policies/strategies** using the framework’s experiment + evaluation tooling.

## What this repo is for
- Implement queueing **environments/simulators** (state, transitions, events)
- Define queueing **decision points** (e.g., which job to serve next, routing, admission control)
- Produce **metrics** that the framework can evaluate (wait time, latency, throughput, utilization, fairness)

## What this repo is NOT
- A new policy evaluation framework
- A UI app or production scheduling system

## Planned components
- Queueing domain types (jobs, servers, queues, events)
- Deterministic baseline environments (easy to test)
- Stochastic workloads (configurable RNG seeds)
- Policy hooks (FCFS, SJF, Priority, Round Robin, etc.) implemented through the framework’s policy interface
- Experiment configs + reproducible runs
