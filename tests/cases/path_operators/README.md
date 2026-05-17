---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "Claude Opus 4.7 (1M context) via Claude Code"
  date: "2026-05-15"
---

# tests/cases/path_operators

End-to-end fixtures for the SHACL property-path operators introduced in
Phase 2C. Each case exercises the path-UNION extension in
`TravSHACL/core/ShapeParser.py` and the corresponding `PathExpression`
AST emission through the full validation pipeline.

| Case | Operator(s) | Shape | Expected contrast |
|---|---|---|---|
| case1 | `sh:alternativePath` | `:ClassA` with `sh:alternativePath ( test:property0 test:property1 )` + `sh:minCount 1` | Instance lacking both properties is invalid |
| case2 | `sh:alternativePath` + `sh:inversePath` (nested) | `:ClassA` with `sh:alternativePath ( [ sh:inversePath test:toA ] test:property0 )` + `sh:minCount 1` | Instance with no incoming toA AND no property0 is invalid |

## Note on Kleene operators (`*`, `+`, `?`)

The four PathExpression AST classes scaffolded in P2C — Alternative,
ZeroOrMore, OneOrMore, ZeroOrOne — are unit-tested in
`tests/test_path_ast.py` for round-trip and `to_sparql()` correctness.
End-to-end fixtures for the three Kleene operators (`*`, `+`, `?`) are
intentionally NOT included here.

The reason: the project's HTTP SPARQL endpoint is Virtuoso (configured
at `http://localhost:8899/sparql`). Virtuoso enforces a "transitive
start" requirement on unbounded property paths — a SPARQL query of the
form `?x <iri>+ ?o` (or `*`, `?`) with both ends unbound raises:

> Virtuoso 37000 Error TR…: transitive start not given

The Trav-SHACL constraint-query generator emits SPARQL with both ends
unbound (the outer wrapper anchors `?x` via `?x a <ClassA>` but
Virtuoso's optimizer does not push that binding into the inner SELECT).
Alternative and Inverse do NOT require anchoring; they are exercised
end-to-end above. Full Kleene-operator end-to-end coverage is deferred
to environments without the Virtuoso anchor constraint (a future Jena
or Apache Fuseki endpoint, or a fixture restructuring that anchors
`?x` via VALUES injection).

JSON shape format is skipped for these fixtures per Q-03 carry-over —
JSON does not encode the new path operators.
