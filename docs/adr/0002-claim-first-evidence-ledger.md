# ADR 0002: Claim-first evidence ledger

## Status
Accepted

## Context
A generic map-layer product is not the differentiator. The product must resolve intent-specific decision claims while preserving uncertainty and source caveats.

## Decision
Use evidence records as the basis for all interpreted claims. Claims cannot exist without evidence links. Source failures are evidence.

## Consequences
- Rule engine comes after evidence ledger.
- Report language must remain cautious and source-linked.
- Tests must check evidence-before-claim behavior.
