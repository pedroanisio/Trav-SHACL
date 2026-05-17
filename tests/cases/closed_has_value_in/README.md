---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "Claude Opus 4.7 (1M context) via Claude Code"
  date: "2026-05-15"
---

# tests/cases/closed_has_value_in

End-to-end fixtures for SHACL §4.8 constraints: `sh:hasValue` and
`sh:in`. `sh:closed` and `sh:ignoredProperties` parser dispatch is
verified via `tests/test_parser_registry.py`; end-to-end fixture
coverage for sh:closed is deferred — see limitation below.

| Case | IRIs exercised | Status |
|---|---|---|
| case1 | `sh:hasValue` | end-to-end |
| case2 | `sh:in` | end-to-end |

## Known limitations

- **`sh:closed` end-to-end fixture is omitted.** Codex's
  `ClosedConstraint.emit_filter` was scaffolded as part of P2C with
  the Q-09 post-parse pass (allowed paths pre-computed at parse
  time), but the engine integration (FILTER NOT EXISTS for any
  property outside the allowed set) interacts with the rule-based
  saturation in ways that are not exercised by any existing fixture.
  Authoring a sh:closed fixture surfaces engine paths similar to
  AndConstraint's that require Phase 3 attention. Parser-level
  dispatch verified via `tests/test_parser_registry.py`.

JSON shape format is skipped for these fixtures per Q-03 carry-over.
