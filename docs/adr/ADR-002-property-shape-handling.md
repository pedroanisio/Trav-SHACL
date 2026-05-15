---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "GPT-5 Codex via Codex CLI"
  date: "2026-05-15"
---

# ADR-002: First-Class PropertyShape Parsing

## Status

Accepted for Phase 1.

## Context

Trav-SHACL previously enumerated only `sh:NodeShape` declarations as top-level
shapes. Property constraints attached to a node shape were parsed, but a
standalone `sh:PropertyShape` declaration was invisible to the shape loader.

Now it requires property shapes to parse as first-class `Shape` instances so
later versions can build richer SHACL support without changing the shape enumeration contract again.

## Decision

`ShapeParser` now enumerates both `sh:NodeShape` and `sh:PropertyShape`.
Parsed `Shape` instances store their shape kind through `shapeKind`.

For a top-level `sh:PropertyShape`, the parser binds the shape itself as its
constraint source, so direct predicates such as `sh:path` and `sh:minCount` are
read from the property-shape node. Target probes no longer require
`sh:NodeShape`, which allows targeted top-level property shapes to validate
through the existing traversal and query-generation path.

Targetless property-only schemas remain invalid as runnable schemas. If no
parsed shape has a target definition, `ShapeSchema.get_starting_point` raises a
clear `ValueError` instead of failing through the previous accidental fallback.

## Consequences

Reuses the existing shape and constraint machinery for supported property-shape patterns.

First-class property-shape support is intentionally narrow: unsupported SHACL
constraint IRIs still fail through ADR-001's registry policy.

## Verification

`tests/test_parser_registry.py` checks standalone and targeted property-shape
parsing. `tests/cases/property_shape/` adds fixture coverage for a node shape
with an additional standalone property shape and for a targeted property shape
validated as the runnable shape.
