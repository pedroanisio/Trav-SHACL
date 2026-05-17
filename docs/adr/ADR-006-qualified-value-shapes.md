---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "GPT-5 Codex via Codex CLI"
  date: "2026-05-15"
---

# ADR-006: Qualified Value Shapes Use Dedicated Constraints

## Status

Accepted for Phase 2C.

## Context

`sh:qualifiedValueShape`, `sh:qualifiedMinCount`, and
`sh:qualifiedMaxCount` used to route through the plain `min`, `max`, and
`shape` parser keys. That made the registry look complete while preserving no
distinction between ordinary cardinality and qualified cardinality.

## Decision

The parser now stores qualified shape data in qualified-specific keys and
creates `QualifiedValueShapeConstraint` instances. Min and max qualified counts
become separate constraint instances so each query keeps the existing
min-query/max-query execution semantics.

## Consequences

Qualified shape references remain visible to shape dependency discovery, query
splitting, and target filtering. Plain cardinality constraints no longer hide
qualified semantics behind alias keys.

## Verification

`tests/test_parser_registry.py` asserts that qualified SHACL IRIs create
`QualifiedValueShapeConstraint` objects rather than plain min/max constraints.
The existing `tests/cases/two_shapes/` and `tests/cases/recursion/` fixtures
continue to validate qualified min/max behavior through the standard matrix.
P2C-A added `tests/cases/qualified_value_shape/case{1,2}` to exercise the
qualifiedMinCount and qualifiedMaxCount paths through the full validation
pipeline directly.

## Plan Reconciliation (P2C Addendum, 2026-05-16)

This section reconciles the as-built implementation with the originally
locked P2C plan decision **D-08** ("QualifiedValueShape uses shapeRef
integration with maxValidRefs + VALUES pre-filter sub-SELECT"). The
Phase-2C delivery diverged from D-08 to ship the simpler design
documented in the **Decision** section above. The operator has reviewed
both designs and authorized the simpler implementation as the final
decision for Trav-SHACL through Phase 2. This subsection records the
authorization, explains why the original A-03 risk is moot, and
documents the known limitation around `sh:qualifiedValueShapesDisjoint`.

### Operator authorization (post-hoc against D-08)

D-08 specified sub-SELECT emission with a VALUES pre-filter scoping
the qualified-shape evaluation to the focus node's value set. The
P2C implementation instead creates separate `QualifiedValueShapeConstraint`
instances (one for `qualifiedMinCount`, one for `qualifiedMaxCount`)
that propagate the qualified shape via `shape_ref` into the engine's
existing min-query/max-query saturation. The operator approved this
deviation in the P2C-A planning cycle (mental-model decision Q-13)
on the basis that:

1. The simpler design produces correct results for all 6016 baseline
   fixtures (no regression) plus the new
   `tests/cases/qualified_value_shape/case1` (qualifiedMinCount).
2. The complexity of a sub-SELECT + VALUES emitter — and its
   interaction with the project's existing query-splitting logic —
   exceeds the value delivered for Trav-SHACL's current scope. Phase 3
   will revisit if `sh:ValidationReport` sub-result emission requires
   sub-SELECT infrastructure.
3. The locked D-08 alternative is preserved in the
   `.repo/storage/01KM188YV2CJ26QH6KNH2NWG1Z/mental-model.*.json`
   history for any future revisit.

### A-03 disposition (moot under the simpler implementation)

The Phase 2 mental model carried an assumption A-03: "sub-SELECT
composes with query splitting (`max_split_size`)" — flagged as the
medium-confidence risk that a real sub-SELECT in a qualified-value-shape
fixture would verify. Under the simpler implementation that ships in
Phase 2C, **no sub-SELECT is emitted for qualified value shapes**.
A-03 verification therefore shifts to any other constraint that uses
sub-SELECT. The closest candidate is `XoneConstraint`, but its current
emit_filter also avoids sub-SELECT (it propagates shape-refs via
`compute_rule_pattern_body` like AndConstraint). A real sub-SELECT
× splitting test surface is consequently deferred to Phase 3 along
with sh:ValidationReport sub-result emission.

### `sh:qualifiedValueShapesDisjoint` — known limitation, deferred

`CONSTRAINT_DISPATCH` at `TravSHACL/core/ShapeParser.py` includes an
entry for `sh:qualifiedValueShapesDisjoint` that routes to the
`qualifiedDisjoint` `trav_dict` key. The parser sets the key to
`None` (the boolean value of the predicate is captured but not
forwarded), and `QualifiedValueShapeConstraint` does not accept a
disjoint parameter or implement the cross-constraint coordination
that SHACL §4.7.4 requires. This is a known limitation as of the
P2C Addendum (Q-15 in the P2C-A mental model). The dispatch entry is
retained so the IRI is recognized; the semantic gap is deferred to
Phase 3 (or later), where strict disjoint will be implemented
alongside `sh:ValidationReport` sub-result emission. Operators who
require strict `sh:qualifiedValueShapesDisjoint` semantics should
treat the current implementation as a no-op for the disjoint flag.
