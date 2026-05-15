---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "GPT-5 Codex via Codex CLI"
  date: "2026-05-15"
---

# ADR-008: Complex Paths Are Parser-Built AST Nodes

## Status

Accepted for Phase 2C.

## Context

`PathExpression.from_string()` is intentionally small. It preserves legacy
support for predicate strings, inverse path strings, and slash-separated
sequence strings. Extending it into a full SHACL path parser would require a
second grammar beside the Turtle/RDF parser.

## Decision

Complex SHACL paths are built from RDF structures in `ShapeParser`:
`Alternative`, `ZeroOrMore`, `OneOrMore`, and `ZeroOrOne`. `from_string()`
remains limited to the legacy string forms.

## Consequences

There is one construction site for SHACL blank-node path expressions, and
string parsing stays backward-compatible. Future nested path operators should
extend `ShapeParser.parse_path_node()` rather than broadening
`PathExpression.from_string()`.

## Verification

`tests/test_path_ast.py` covers the new AST nodes. `tests/test_parser_registry.py`
asserts that Turtle blank-node path expressions parse into those nodes and emit
the expected SPARQL property-path syntax.
