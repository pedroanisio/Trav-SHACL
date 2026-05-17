---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "Claude Opus 4.7 (1M context) via Claude Code"
  date: "2026-05-15"
---

# tests/cases/logical_constraints

End-to-end fixtures for the SHACL §4.6 logical operators implemented
in Phase 2C and the P2C Addendum.

| Case | Operator | Inner | Status |
|---|---|---|---|
| case1 | `sh:not` | `sh:path test:property2 ; sh:minCount 1` (negates "has property2") | end-to-end |
| case2 | `sh:not` | `sh:path test:property1 ; sh:minCount 1` (negates "has property1") | end-to-end |

## Engine fix applied in P2C-A

`NotConstraint` shipped in P2C but its `emit_filter` was parser-correct
and engine-broken: the `EXISTS { ... }` filter was wrapped around the
inner sub-pattern without binding the focus variable in the outer
WHERE clause. Result: the maxQuery's SPARQL had an unbound `?x` in the
FILTER and returned zero rows for every shape, so the engine could
not invalidate any focus.

The fix (P2C-A): `NotConstraint.emit_filter` now emits the nested
constraint's pattern directly into the parent builder (binding `?x`
through the inner constraint's triple emission). Combined with
`max=0`, the engine's existing cardinality logic correctly invalidates
foci where the inner pattern matches. See
[ADR-007-sh-not-architecture.md](../../../docs/adr/ADR-007-sh-not-architecture.md)
for the architectural decision.

## Known limitations exercised here

- **AndConstraint end-to-end fixture intentionally omitted.** The
  parser-level construction of `AndConstraint` (over shape references
  only) works correctly. End-to-end fixture authoring revealed the
  engine's rule-pattern saturation does not correctly intersect
  shape-ref propagations from AndConstraint's
  `compute_rule_pattern_body` — every focus ends up invalid. The
  engine-integration fix requires substantive work in
  `Validation.interleave` / `apply_rules` that is out of scope for
  P2C-A. Deferred to Phase 3 alongside sh:ValidationReport
  sourceConstraintComponent mapping.
- **XoneConstraint end-to-end fixture intentionally omitted** (same
  root cause as AndConstraint — XoneConstraint inherits AndConstraint's
  shape-ref propagation pattern). Parser dispatch verified via
  `tests/test_parser_registry.py::test_xone_constraint_is_constructed_from_sh_xone`
  and `::test_xone_constraint_over_atomic_inner_raises_not_implemented`.
- **Shape-reference `sh:not`** raises `NotImplementedError` per DEC-05.

JSON shape format is skipped for these fixtures per Q-03 carry-over.
