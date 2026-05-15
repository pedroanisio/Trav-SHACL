---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "GPT-5 Codex via Codex CLI"
  date: "2026-05-15"
---

# ADR-005: Pair Constraints Use a Separate Referenced Property

## Status

Accepted for Phase 2B.

## Context

SHACL property-pair constraints compare values from two property paths:
`sh:path` and a second path carried by `sh:equals`, `sh:disjoint`,
`sh:lessThan`, or `sh:lessThanOrEquals`.

Trav-SHACL already has `shapeRef` for inter-shape references. Reusing that
field for the second property path would corrupt the shape dependency graph,
because pair constraints reference another property, not another shape.

## Decision

`Constraint` now has `referencedProperty`, parsed as a `PathExpression`, and
`referenced_property_sparql()` for query emission. Pair constraints store the
second path there and leave `shapeRef` unset.

## Consequences

Shape dependency discovery remains limited to real shape references. Future
constraints that need a second property path can reuse the same field without
teaching `Shape` or `QueryGenerator` about concrete pair-constraint classes.

## Verification

`tests/test_parser_registry.py` asserts that pair constraints keep
`shapeRef` empty and expose the second path through
`referenced_property_sparql()`. `tests/cases/pair_constraints/` validates the
pair constraints through the normal fixture path.
