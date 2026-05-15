---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "GPT-5 Codex via Codex CLI"
  date: "2026-05-15"
---

# ADR-004: PathExpression AST for SHACL Paths

## Status

Accepted for Phase 2A.

## Context

Trav-SHACL represented paths as raw strings. That was enough for predicate
paths, but it made inverse and sequence paths indistinguishable from
string-formatting conventions inside parser and query-generation code.

## Decision

Parsed constraints now store a `PathExpression` object. The initial AST is
intentionally small:

- `Predicate` for direct predicate paths.
- `Inverse` for `sh:inversePath`.
- `Sequence` for RDF-list sequence paths.

The AST preserves legacy SPARQL text through `to_sparql()`, so existing query
generation can remain stable while path handling gains a typed internal
boundary.

## Consequences

Parser code must convert incoming path text into `PathExpression` objects, and
query-generation code must emit paths through `path_sparql()` or
`to_sparql()`. Comparing path references now compares the emitted SPARQL form
instead of object identity.

## Verification

`tests/test_path_ast.py` covers predicate, inverse, sequence, and malformed
sequence paths. Parser and fixture tests cover path emission through shape
validation.
