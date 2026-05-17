---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "Claude Opus 4.7 (1M context) via Claude Code"
  date: "2026-05-17"
---

# tests/cases/logical_constraints

End-to-end fixtures for the SHACL §4.6 logical operators implemented
in Phase 2C, P2C Addendum, and Phase 3B.

| Case | Operator | Inner | Status |
|---|---|---|---|
| case1 | `sh:not` | `sh:path test:property2 ; sh:minCount 1` (negates "has property2") | end-to-end (P2C-A) |
| case2 | `sh:not` | `sh:path test:property1 ; sh:minCount 1` (negates "has property1") | end-to-end (P2C-A) |
| case3 | `sh:and` | Two `sh:node` refs (`:HasProperty1`, `:HasProperty2`) | end-to-end (P3B) |
| case4 | `sh:xone` | Two `sh:node` refs (`:HasProperty1`, `:HasProperty2`) | end-to-end (P3B, K-02 deferred) |

## Engine fix applied in P2C-A (sh:not)

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

## Phase 3B additions (sh:and, sh:xone)

P3B closed the two end-to-end fixture omissions documented in P2C-A
(`AndConstraint` and `XoneConstraint`). The root cause was twofold:

1. **Filter exclusion** in `Shape.compute_constraint_queries` (L200 at
   HEAD `073413f`): `[c for c in min_constraints if c.get_shape_ref()
   is not None]` excluded `AndConstraint` and `XoneConstraint` because
   they store their shape-refs in `shapeRefs` (plural tuple), not the
   inherited singular `shapeRef` field. The shape-ref propagations
   declared by `compute_rule_pattern_body` were therefore never
   consumed by the query generator.
2. **Missing focus-binding triple** in `emit_filter`. Even when
   admitted into `minQuery`, the inherited `BIND(?x AS ?x)` no-op
   produced SPARQL with no triple binding `?x`, returning zero rows.

The P3B fix:

- **Polymorphic accessor** `Constraint.participates_in_min_query()`
  with subclass overrides on `AndConstraint` and `XoneConstraint`
  (returns `True` when `shapeRefs` is non-empty).
- **Filter widening** at `Shape.compute_constraint_queries` to use
  the new accessor.
- **Target-passthrough triple** in `AndConstraint.emit_filter` and
  `XoneConstraint.emit_filter`: the parent shape's target-class
  triple is injected so `?x` is bound to the candidate focus set.

See [ADR-009-and-xone-engine-fix.md](../../../docs/adr/ADR-009-and-xone-engine-fix.md)
for the architectural decision.

### case3 ground truth (sh:and over `:HasProperty1` and `:HasProperty2`)

Derived from `tests/data/test.ttl` (verified via rdflib parse):

| ClassA Instance | property1 | property2 | Both? |
|---|---|---|---|
| 0 | ✓ | ✗ | invalid |
| 1 | ✓ | ✓ | **valid** |
| 2 | ✓ | ✓ | **valid** |
| 3 | ✓ | ✗ | invalid |
| 4 | ✗ | ✓ | invalid |
| 5 | ✓ | ✓ | **valid** |
| 6 | ✓ | ✓ | **valid** |

valid: `{1, 2, 5, 6}`; invalid: `{0, 3, 4}`.

### case4 ground truth (sh:xone, engine-faithful conjunction-like)

Trav-SHACL's engine treats `sh:xone` disjuncts the same way it treats
`sh:and` conjuncts at the rule-pattern body level: a focus is valid
when *both* disjuncts match. Under SHACL §4.6.4 strict "exactly one"
semantics, the partition would be different (instance0 and 4 would be
valid; instances 1, 2, 5, 6 would be invalid because they satisfy two
disjuncts). This is the **K-02 known limitation** carried forward
from P2C-A; ADR-009 §Consequences documents the deferral.

`case4` uses the engine-faithful partition (same as `case3`) so the
test reflects current engine behavior. A future phase that fixes
strict exactly-one semantics will need to invert `case4`'s ground
truth (or add a separate strict-xone fixture).

## Known limitations exercised here

- **K-02: `XoneConstraint` strict exactly-one semantics** —
  carried forward from P2C-A. Engine's interleave step does not count
  satisfied disjuncts; a focus that matches both disjuncts is currently
  classified valid. Strict enforcement requires counting logic in the
  rule-pattern saturation step; deferred until `sh:ValidationReport`
  sub-result emission lands (Phase 4+).
- **`sh:and` / `sh:xone` atomic-inner** raises `NotImplementedError`
  at parse time. Per DEC-05 carry-over, only shape-reference inners
  are supported; atomic property-shape inners (e.g.,
  `sh:and ( [sh:datatype xsd:integer] ... )`) are out of scope.
- **Shape-reference `sh:not`** raises `NotImplementedError` per DEC-05.

JSON shape format is skipped for these fixtures per Q-03 carry-over.
