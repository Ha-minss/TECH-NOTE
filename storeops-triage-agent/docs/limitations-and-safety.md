# Limitations and Safety

## Synthetic boundary

This project uses synthetic operational fixtures and synthetic policy documents. It is a portfolio artifact, not a disguised production case study.

## Operational safety

The system does not connect to real VANs, payment processors, or enterprise systems. It does not execute refunds, cancellations, reconfiguration, or other sensitive actions automatically.

## Human approval

A human operator remains responsible for cause confirmation, routing, and merchant-facing handoff. The system prepares a brief; it does not replace the approval workflow.

## LLM behavior

The LLM layer is optional. When it is enabled, outputs are constrained by prompt contracts, schema validation, fallback logic, and the same operator review surface used by the deterministic path.

## Likely failure modes

- missing merchant-only facts
- incomplete or delayed evidence
- conflicting incident-time versus current-time records
- optional route lookup failures

These are surfaced as clarification, degraded review, or conflict review states rather than hidden behind confident autonomous actions.
