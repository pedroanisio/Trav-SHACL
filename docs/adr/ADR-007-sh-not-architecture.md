---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "GPT-5 Codex via Codex CLI"
  date: "2026-05-15"
---

# ADR-007: `sh:not` Supports Atomic Property Shapes First

## Status

Accepted for Phase 2C.

## Context

Trav-SHACL validates by compiling constraints into SPARQL queries plus rule
patterns. Negating an arbitrary shape reference is not equivalent to flipping a
single constraint flag: it changes how the engine combines shape-level
dependencies and target classifications.

## Decision

Phase 2C implements `sh:not` for atomic property-shape expressions by emitting
a violation query with an `EXISTS` block over the nested property pattern.
Shape-reference `sh:not` raises `NotImplementedError` instead of silently
claiming support.

## Consequences

The supported `sh:not` subset is executable and explicit. The unsupported
shape-reference case is fail-fast, preserving PALS-style truthfulness until the
engine has a complete rule-level representation for shape negation.

## Verification

`tests/test_parser_registry.py` asserts that shape-reference `sh:not` raises
`NotImplementedError`. Atomic property-shape negation is represented by
`NotConstraint` and emitted through the same polymorphic query-builder path as
the other constraints.
