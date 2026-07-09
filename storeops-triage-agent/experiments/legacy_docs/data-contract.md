# Data Contract

This document describes the synthetic data model used by the workflow, tools, and evaluation system.

## Core rules

- operational tables contain raw facts, not diagnoses
- `root_cause` belongs in evaluation metadata, not in operational rows
- `store_id` is required for all store-scoped operational records
- `tool_failure_injections` are modeled separately from operational business data

## Scenario coverage

The data contract supports the same scenario set named in the scenario contract: `S1`, `S2`, `S3`, `S4`, `S5`, `S6A`, `S6B`, and `S7`.

## Provenance and freshness

Every normalized tool response preserves source provenance and freshness metadata so the workflow can reason about stale, delayed, or conflicting evidence safely.
