---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "GPT-5 Codex via Codex CLI"
  date: "2026-05-15"
---

# ADR-003: Constraint-Owned QueryBuilder Dispatch

## Status

Accepted for Phase 2A.

## Context

`QueryGenerator` previously selected behavior with concrete class checks for
`MaxOnlyConstraint` and the base `Constraint`. That made query generation
depend on the current class hierarchy and forced later SHACL constraint work to
modify the central query builder whenever a new constraint class appeared.

## Decision

Constraints now expose query-generation behavior through methods on the
constraint API:

- `emit_filter(...)` adds the triples and filters for a constraint.
- `is_max_only_constraint()` declares the max-only branch used by OR and max
  query generation.
- `is_sparql_constraint()` identifies SPARQL constraints without importing the
  concrete subclass into `Shape`.

`QueryBuilder.build_clause()` delegates to the constraint rather than testing
for concrete classes.

## Consequences

New constraint classes can participate in query generation by implementing the
constraint API. The query builder remains responsible for assembling SPARQL
strings, but constraint-specific emission no longer requires central type
switches.

## Verification

`tests/test_parser_registry.py`, `tests/test_path_ast.py`, and the existing
fixture matrix cover dispatch compatibility. The drift guard suite checks that
class-based dispatch does not return to `QueryGenerator` or `Shape`.
