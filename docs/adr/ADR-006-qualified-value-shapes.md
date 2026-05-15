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
