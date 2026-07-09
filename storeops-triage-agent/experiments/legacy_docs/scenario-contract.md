# Scenario Contract

This document defines the synthetic scenario set used by the offline payment domain pack.

## Purpose

The scenario contract is the shared source of truth for fixture design, expected workflow states, required tool usage, and safety behavior.

## Implemented scenarios

- `S1`: duplicate TID after new terminal activation
- `S2`: terminal identifier mismatch
- `S3`: incomplete VAN merchant registration
- `S4`: POS-Front connection issue
- `S5`: merchant-only clarification required
- `S6A`: required tool failure
- `S6B`: optional route lookup failure
- `S7`: temporal evidence conflict

## Tool and evidence rules

- `required_tools` are necessary before the system can emit a grounded likely assessment
- `forbidden_tools` are unnecessary or unsafe for the case
- workflow states such as `NEEDS_CLARIFICATION`, `DEGRADED_REVIEW`, and `CONFLICT_REVIEW` are part of the contract, not fallback accidents

## Global safety rules

- no automatic TID change
- no refund or cancellation execution
- no VAN registration mutation
- no autonomous external handoff without human approval
