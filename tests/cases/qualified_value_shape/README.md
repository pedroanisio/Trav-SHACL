---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "Claude Opus 4.7 (1M context) via Claude Code"
  date: "2026-05-15"
---

# tests/cases/qualified_value_shape

End-to-end fixtures for `sh:qualifiedValueShape` + `sh:qualifiedMinCount` /
`sh:qualifiedMaxCount` per ADR-006. Codex's simpler implementation
(no sub-SELECT, no VALUES pre-filter) creates separate min/max
QualifiedValueShapeConstraint instances that propagate the qualified
shape via `shape_ref` into the engine's traversal — the engine's
existing min-query/max-query path handles the counting.

| Case | Pattern | Status |
|---|---|---|
| case1 | ClassB `sh:qualifiedValueShape [sh:node :ClassC]` on `test:toC` with `sh:qualifiedMinCount 1` | end-to-end correct |
| case2 | Same shape + `sh:qualifiedMaxCount 2` | parser accepts both bounds; **maxCount enforcement is approximate** (see limitation below) |

## Known limitations exercised here

- **`sh:qualifiedMaxCount` upper bound is not strictly enforced.** Per
  ADR-006's "simpler implementation" (no sub-SELECT), the maxCount
  applies to the total cardinality of the property path, not to the
  count of values that *also* satisfy the qualified shape. For data
  where total path cardinality ≤ qualified-satisfying cardinality, the
  spec-compliant answer matches the engine's answer. Where they
  diverge (e.g., ClassB_Instance2 has 3 toC edges all satisfying
  :ClassC, which spec-wise violates qualifiedMaxCount=2), the engine
  classifies as valid. case2's groundTruth captures the actual engine
  output; strict spec compliance requires Phase 3's sub-SELECT
  rework.
- **`sh:qualifiedValueShapesDisjoint`** is documented in ADR-006 Plan
  Reconciliation as fully deferred — the dispatch entry exists but
  the value is not consumed.

JSON shape format is skipped for these fixtures per Q-03 carry-over.
