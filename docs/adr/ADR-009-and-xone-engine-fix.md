---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "Claude Opus 4.7 (1M context) via Claude Code"
  date: "2026-05-17"
---

# ADR-009: AndConstraint / XoneConstraint Engine Participation

## Status

Accepted for Phase 3B (HEAD after Phase 3A `073413f`).

## Context

P2C-A delivered parser dispatch for `sh:and` and `sh:xone` over node-shape
references, but end-to-end fixtures were intentionally omitted because of an
engine saturation bug: every focus was classified invalid. P3A
(`073413f`, "feat: implement phase 3a shacl validation report serializer")
delivered the spec-conformant `sh:ValidationReport` serializer and locked
Q-19: the engine fix is in scope for Phase 3B.

Codebase inspection during the P3B mental-model refresh
([`mental-model.latest.json`](../../.repo/storage/01KM188YV2CJ26QH6KNH2NWG1Z/mental-model.latest.json))
revised the P3A handoff hypothesis. The bug had **two layers**, not one:

1. **Filter exclusion** at
   [`Shape.compute_constraint_queries`](../../TravSHACL/core/Shape.py)
   L200: `[c for c in min_constraints if c.get_shape_ref() is not None]`
   excluded `AndConstraint` and `XoneConstraint` from `minQuery`
   construction because they store shape-refs in `shapeRefs` (plural
   tuple), not the inherited singular `shapeRef` field. Their
   `compute_rule_pattern_body` propagations were therefore never
   consumed by `QueryGenerator.compute_rule_pattern`.
2. **Missing focus-binding triple** in `emit_filter`. Even when admitted
   into `minQuery`, the pre-P3B `BIND(?x AS ?x)` no-op produced SPARQL
   with no triple binding `?x`. The endpoint returned zero rows, the
   interleave step received no answers, and the focus was classified
   invalid by saturation default.

The P3A handoff identified candidate (a) (target-passthrough triple in
`emit_filter`) as the recommended fix, with `NotConstraint`'s P2C-A
emit_filter as the precedent. Codebase inspection confirmed (a) is
necessary but not sufficient: the filter widening at L200 is the
load-bearing complement.

## Decision

**Two-layer polymorphic fix:**

1. Add `Constraint.participates_in_min_query()` accessor with default
   `return self.shapeRef is not None`. This preserves pre-P3B semantics
   for all 25 subclasses that hold their shape-ref in the inherited
   singular field.
2. Override on `AndConstraint` and `XoneConstraint` to return
   `len(self.shapeRefs) > 0`. This admits these two subclasses into
   `minQuery` participation via the same polymorphic surface.
3. Change `Shape.compute_constraint_queries` L200 from
   `c.get_shape_ref() is not None` to `c.participates_in_min_query()`.
4. Replace `AndConstraint.emit_filter` and `XoneConstraint.emit_filter`
   BIND no-op with a target-passthrough triple emission. The implementation
   extracts the parent shape's target-class triple from
   `builder.target_query` via `get_target_node_statement` (an existing
   helper at
   [`TravSHACL/sparql/QueryGenerator.py`](../../TravSHACL/sparql/QueryGenerator.py)
   L14) and appends it to `builder.triples`. The de-duplication check
   (`if target_body not in builder.triples`) keeps the query well-formed
   when multiple shape-ref constraints share a parent.

This preserves the **DEC-04 polymorphic dispatch invariant** (no
`isinstance(*Constraint)` reintroduced in `QueryGenerator`, `Shape`,
`Validation`, `InstancesRetrieval`). The drift guard
`test_constraint_dispatch_stays_polymorphic` (with `allowed = set()`)
continues to pass.

## Alternatives Rejected

**(b) Base-triple injection in `Shape.compute_constraint_queries`.**
Always inject `?x ?p ?o` (or equivalent open triple) into `minQuery`
when no constraint contributes a binding for `?x`. *Rejected:* changes
the query shape for every constraint family; risks spurious focus-node
enumeration on large data graphs because the open triple matches every
subject in the dataset.

**(c) Engine-level handling of empty-body `minQuery`.** Detect the
zero-binding case in `Validation.interleave` and fall back to the
target query's focus set as the candidate set. *Rejected:* silently
masks future bugs of the same class; reduces the engine's ability to
surface query-construction defects.

**(d) `emit_filter` re-emits the inner shape-refs' atomic triples.**
Mirror `NotConstraint.emit_filter` directly. *Rejected on inspection:*
`AndConstraint`/`XoneConstraint` inners are *shape references* via
`sh:node`, not inline atomic property shapes. The inner shape may have
arbitrary structure (other path expressions, qualifiers, nested
logical operators) that emitting transitively would require resolving
through the full shape graph at query-build time. Target-passthrough
keeps the engine's interleave step responsible for combining the
shape-ref propagations declared by `compute_rule_pattern_body`.

## Consequences

### Resolved

- `sh:and` end-to-end (`tests/cases/logical_constraints/case3`):
  2 shape-ref conjuncts over `:HasProperty1` and `:HasProperty2`.
  Ground truth `valid={1,2,5,6}` / `invalid={0,3,4}`, derived from
  `tests/data/test.ttl` (verified via rdflib parse). 64 fixture
  invocations pass under the full parametrize matrix.
- `sh:xone` end-to-end (`tests/cases/logical_constraints/case4`):
  2 shape-ref disjuncts over the same inner shapes. Engine-faithful
  partition matches `case3` (see K-02 below). 64 fixture invocations
  pass.

### Carried Forward (K-02 — strict exactly-one semantics)

Trav-SHACL's engine treats `sh:xone` disjuncts the same way it treats
`sh:and` conjuncts at the rule-pattern body level: a focus is valid
when both disjuncts match. Under SHACL §4.6.4 strict "exactly one"
semantics, the partition would invert (instances satisfying both
disjuncts would be invalid; instances satisfying exactly one would be
valid). P3B does not fix this — `case4`'s ground truth reflects the
engine-faithful classification, not strict xone.

Strict exactly-one enforcement requires:

- Engine support for *counting* satisfied disjuncts during interleave.
- A new `compute_rule_pattern_body` shape for `XoneConstraint` that
  encodes the cardinality requirement at the rule level.

K-02 is deferred until `sh:ValidationReport` sub-result emission lands
(Phase 4+). A future contributor implementing strict-xone will need to
invert `case4`'s ground truth or add a separate strict-xone fixture.

### Carry-overs (unchanged)

- **DEC-05**: shape-reference `sh:not` remains `NotImplementedError`
  (atomic-only); `sh:and` / `sh:xone` atomic-inner remain
  `NotImplementedError` (shape-ref-only).
- **DEC-04**: polymorphic dispatch invariant preserved.
- **Q-16**: `ShapeSchema.validate(report_format=None)` returns the dict
  byte-identically (P3B does not touch the signature).
- **Q-17**: per-class `SOURCE_COMPONENT` mapping unchanged.

## Ground-Truth Derivation

`tests/data/test.ttl` ClassA instances (verified via rdflib parse):

| Instance | `property1` | `property2` | Source line(s) |
|---|---|---|---|
| 0 | ✓ | ✗ | L3-7 |
| 1 | ✓ | ✓ | L9-16 |
| 2 | ✓ | ✓ | L18-29 |
| 3 | ✓ | ✗ | L31-43 |
| 4 | ✗ | ✓ | L45-46 |
| 5 | ✓ | ✓ | L48-53 |
| 6 | ✓ | ✓ | L55-61 |

case3 (`sh:and`):
- valid (both properties): `{1, 2, 5, 6}`
- invalid (either missing): `{0, 3, 4}`

case4 (`sh:xone`, engine-faithful):
- valid (both properties, per current engine): `{1, 2, 5, 6}`
- invalid (≠ both): `{0, 3, 4}`

case4 strict-xone (deferred K-02 reference):
- valid (exactly one): `{0, 3, 4}`
- invalid (zero or two): `{1, 2, 5, 6}`

## References

- [ADR-007: sh:not architecture](ADR-007-sh-not-architecture.md) —
  P2C-A `emit_filter` precedent.
- [ADR-008: Complex paths are parser-built AST nodes](ADR-008-path-from-string-scope.md) —
  unrelated to this fix; cited for ADR-numbering continuity.
- [HANDOFF-phase-3a-to-3b.md](../../.repo/storage/01KM18ZD23GC3TDVN7W0GX2000/HANDOFF-phase-3a-to-3b.md) —
  the input handoff that framed P3B; root-cause hypothesis revised
  here based on codebase inspection.
- [HANDOFF-phase-2c-to-phase-3.md](../../.repo/storage/01KM18ZD23GC3TDVN7W0GX2000/HANDOFF-phase-2c-to-phase-3.md) —
  K-02 original deferral context.
- [mental-model.latest.json](../../.repo/storage/01KM188YV2CJ26QH6KNH2NWG1Z/mental-model.latest.json) —
  P3B reasoning trace (revised root-cause analysis).
- [plan-phase-3b.latest.json](../../.repo/storage/01KM18ZD23GC3TDVN7W0GX2000/plan-phase-3b.latest.json) —
  the P3B PlanSchema instance.
- [tests/cases/logical_constraints/README.md](../../tests/cases/logical_constraints/README.md) —
  Phase 3B additions section with the end-to-end fixture description.
