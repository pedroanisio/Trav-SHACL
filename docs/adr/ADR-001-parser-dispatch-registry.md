---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "GPT-5 Codex via Codex CLI"
  date: "2026-05-15"
---

# ADR-001: Full-IRI Parser Dispatch Registry

## Status

Accepted for Phase 1.

## Context

`ShapeParser.parse_all_const` previously classified SHACL predicates by
checking whether lowercased predicate strings contained fragments such as
`min`, `max`, `path`, `datatype`, `valueshape`, or `not`. That made the parser
fragile: adding a legal SHACL IRI such as `sh:minInclusive`, `sh:minLength`, or
`sh:qualifiedMinCount` could silently route to the existing `sh:minCount`
handling.

Phase 1 needs the parser to be safe before Phase 2 adds more SHACL Core
constraint families.

## Decision

Trav-SHACL now dispatches parsed SHACL predicates through explicit full-IRI
registries:

- `CONSTRAINT_DISPATCH` maps supported constraint IRIs to internal parser keys.
- `METADATA_DISPATCH` maps accepted metadata IRIs to additive metadata fields.
- `IGNORED_CONSTRAINT_IRIS` records non-constraint IRIs that may appear while
  reading first-class property shapes.

Unknown constraint IRIs are no longer silently guessed. They raise
`NotImplementedError` by default. When `ignore_errors=True`, they are skipped
with a warning.

## Consequences

New constraint support must add an exact IRI entry before parser branches can
consume it. This is intentionally stricter than the previous behavior because
it converts silent drift into an explicit testable failure.

The registry is not a full SHACL support claim. It only records the IRIs that
the current parser can safely route.

## Verification

The guard test is `tests/test_parser_registry.py`. It covers registry coverage,
unknown IRI behavior, and the absence of substring-based dispatch for new IRIs.
