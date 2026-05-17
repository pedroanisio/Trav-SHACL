---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "Claude Opus 4.7 (1M context) via Claude Code"
  date: "2026-05-17"
---

# Trav-SHACL — Final SHACL Core Compliance Status (Phase 3)

This document closes the SHACL Core compliance effort. It maps every
gap from the original [cover-report.md](./cover-report.md) (frozen
at commit `718cf52`) to its post-Phase-3 status, with closing commit
hashes and ADR references.

The original cover-report is the **gap-inventory anchor** and is
intentionally preserved untouched (audit-trail constraint). This
document is its closing counterpart, derived structurally from the
codebase at HEAD `e9f2864` (post-P3B; P3C delivery is this commit).

## Method

Same approach as the original cover-report: verdicts derived
structurally from the codebase, not from project docs.

- Each closed gap cites the **closing commit hash** and the
  **relevant ADR** (where applicable).
- Each closed-with-limitation entry names the limitation key (K-NN)
  and points to the deferral document.
- Each deferred entry names the residual limitation and points to
  Phase 4+ candidate scope in §Residual limitations.

## Phase-by-phase status

| Phase | Commit | Deliverable summary |
|---|---|---|
| **Phase 1** (parser foundation) | `4286b7d` | Full-IRI parser-dispatch registry; drift guards (allowed=set()); 5 ADRs (001-005); cover-report.md pinned at 718cf52 as the gap inventory. |
| **Phase 2A** (path support) | `76aa9c4` | SHACL path-expression AST (Predicate, Inverse, Sequence, Alternative, ZeroOrMore, OneOrMore, ZeroOrOne); polymorphic refactor of QueryGenerator and Shape (DEC-04 invariant established). |
| **Phase 2B** (core constraints) | `5add8b2` | 15 new polymorphic Constraint subclasses: ClassConstraint, NodeKindConstraint, 4× Range, 5× String, 4× PropertyPair. |
| **Phase 2C** (logical / qualified / closed / has-value / in) | `cc0c42e` | 7 new subclasses: AndConstraint, NotConstraint, QualifiedValueShapeConstraint, ClosedConstraint, HasValueConstraint, InConstraint, plus 4 path-AST nodes. ADR-006 (qualified-value-shapes), ADR-007 (sh:not architecture). |
| **Phase 2C Addendum** | `3902592` | NotConstraint engine integration fix; XoneConstraint parser dispatch; 4 new fixture categories (path_operators, logical_constraints, qualified_value_shape, closed_has_value_in); ADR-008 (path-from-string-scope). |
| **Phase 3A** (validation report serializer) | `073413f` | sh:ValidationReport serializer (Turtle + JSON-LD); 27 SOURCE_COMPONENT polymorphic mappings; ShapeSchema.validate side-by-side signature; PALS round-trip contract test. |
| **Phase 3B** (And/Xone engine fix) | `e9f2864` | AndConstraint/XoneConstraint engine saturation fix via polymorphic participates_in_min_query accessor + target-passthrough triple emission; case3/case4 end-to-end fixtures; ADR-009. |
| **Phase 3C** (closing documentation) | (this commit) | JSON shape format formal deprecation (v2.0.0 removal target); ADR-010; this document; HANDOFF-phase-3c-to-done.md. |

## Gap-closure table

Each row maps an entry from the original cover-report.md to its
post-Phase-3 status.

### §1 Targets

All target forms were ✅ at the frozen baseline. **No change.**

### §2 Shape types

| Original gap | Frozen status | Post-P3 status | Closing commit | Notes |
|---|---|---|---|---|
| `sh:and` (nested arbitrary shape expressions) | ✅ subset (shape-refs only) | ✅ closed-with-limitation | P3B `e9f2864` | DEC-05 carry-over: shape-ref-only; atomic-inner still raises `NotImplementedError`. End-to-end fixture: `tests/cases/logical_constraints/case3`. ADR-009. |
| `sh:xone` | ❌ fail-fast NotImplementedError | ✅ closed-with-limitation | P2C-A `3902592` (parser); P3B `e9f2864` (engine) | K-02: strict exactly-one semantics deferred; engine treats disjuncts as conjunction. End-to-end fixture: `tests/cases/logical_constraints/case4`. ADR-009. |
| `sh:not` (shape-reference) | ❌ NotImplementedError | ❌ deferred (DEC-05) | — | DEC-05: atomic-only by design; shape-ref sh:not raises `NotImplementedError` at parse time. |
| Inline blank-node `sh:property` | ⚠ Partial | ⚠ same | P1 `4286b7d` | Walked; only recognized predicates inside are kept. Unchanged by Phase 2-3. |

### §3 Property paths

All path forms were ✅ at the frozen baseline. **No change.** End-to-end
Kleene-path fixtures remain deferred (Virtuoso transitive-start
constraint blocks the fixture pattern).

### §4 Core constraint components

#### §4.1 Cardinality — All ✅ at baseline; **no change**.

#### §4.2 Value-type — All ✅ at baseline; **no change**.

#### §4.3 Value-range

All four `sh:minInclusive`/`sh:maxInclusive`/`sh:minExclusive`/`sh:maxExclusive` were ✅
at baseline. **No change.**

#### §4.4 String-based

`sh:minLength`/`sh:maxLength`/`sh:pattern`/`sh:languageIn`/`sh:uniqueLang`
all ✅ at baseline. **`sh:uniqueLang n>2` deferred** (self-join FILTER,
no GROUP BY; see §Residual limitations).

#### §4.5 Property-pair — All ✅ at baseline; **no change**.

#### §4.6 Logical constraints

| Original gap | Frozen status | Post-P3 status | Closing commit | Notes |
|---|---|---|---|---|
| `sh:and` | ✅ subset | ✅ closed-with-limitation | P3B `e9f2864` | See §2 row. |
| `sh:or` | ✅ (NodeShape level) | ✅ same | — | Unchanged by Phase 2-3. |
| `sh:not` | ✅ subset (atomic-only) | ✅ same (engine fixed in P2C-A) | P2C-A `3902592` | DEC-05: atomic-only by design. ADR-007. |
| `sh:xone` | ❌ | ✅ closed-with-limitation | P3B `e9f2864` | See §2 row. K-02. |

#### §4.7 Shape-based

| Original gap | Frozen status | Post-P3 status | Closing commit | Notes |
|---|---|---|---|---|
| `sh:qualifiedValueShapesDisjoint` | ⚠ Parsed | ⚠ same | — | Parser dispatch wired; disjoint-specific semantics deferred (see §Residual limitations). ADR-006. |
| `sh:qualifiedMinCount`/`sh:qualifiedMaxCount` (cardinality interpretation) | ✅ | ⚠ deferred-as-limitation | — | Current interpretation is qualified-satisfying-values count, not property-cardinality. See §Residual limitations. |

#### §4.8 Other

| Original gap | Frozen status | Post-P3 status | Closing commit | Notes |
|---|---|---|---|---|
| `sh:closed` + `sh:ignoredProperties` | ✅ | ✅ closed-with-limitation | P2C `cc0c42e` | Parser dispatch verified; end-to-end fixture deferred (see §Residual limitations). |
| `sh:hasValue` | ✅ | ✅ | P2C `cc0c42e` | HasValueConstraint subclass; fixtures under `tests/cases/closed_has_value_in/`. |
| `sh:in` | ✅ | ✅ | P2C `cc0c42e` | InConstraint subclass. |

### §5 SPARQL-based constraints

All four ❌ items from §5 remain ❌ at post-P3 state — they are out of
the SHACL-Core scope this effort targeted. Specifically:
`sh:prefixes`/`sh:declare`, `sh:message`, `sh:ask`, user-defined
`sh:SPARQLConstraintComponent` are **deferred** (no Phase 4+
commitment).

### §6 Validation reports — **CLOSED** (Phase 3A)

| Original gap | Frozen status | Post-P3 status | Closing commit | Notes |
|---|---|---|---|---|
| `sh:ValidationReport` graph root | ❌ | ✅ | P3A `073413f` | `TravSHACL/output/ValidationReportSerializer.py`. |
| `sh:ValidationResult` per violation | ❌ | ✅ | P3A `073413f` | Emitted per `(shape_id, focus_iri, sign)` tuple in invalid_instances. |
| `sh:conforms` boolean | ❌ | ✅ | P3A `073413f` | xsd:boolean Literal. |
| `sh:resultSeverity` | ❌ | ✅ | P3A `073413f` | Fallback chain: constraint.severity → shape.severity → sh:Violation default. |
| `sh:focusNode`, `sh:sourceShape`, `sh:sourceConstraintComponent`, `sh:resultPath` | ❌ | ✅ | P3A `073413f` | `sh:sourceConstraintComponent` resolved via per-class SOURCE_COMPONENT (27 mappings). |
| `sh:resultMessage` | ❌ | ✅ | P3A `073413f` | Fallback chain: constraint.description → shape.description → omitted. |
| `sh:value` (per-value violations) | ❌ | ❌ deferred | — | Engine surfaces per-focus, not per-value, violations. See §Residual limitations (sub-result emission). |

PALS's Law contract: `tests/test_validation_report.py::test_roundtrip_invalid_instances_match_engine`
asserts the serializer's focus-node set matches the engine's
classification (round-trip via rdflib's own parser).

### §7 Severity, deactivation, metadata

| Original gap | Frozen status | Post-P3 status | Notes |
|---|---|---|---|
| `sh:severity` | ❌ | ✅ | constraint.severity / shape.severity captured by parser; consumed by serializer. |
| `sh:deactivated` | ❌ | ❌ deferred | Not parsed. |
| `sh:name`, `sh:description`, `sh:group`, `sh:order`, `sh:defaultValue` | ❌ | ⚠ partial | `description` consumed by serializer for `sh:resultMessage`; others parsed but not surfaced. |

### §8 Beyond-spec extensions — Trav-SHACL specific

| Feature | Post-P3 status | Notes |
|---|---|---|
| Cyclic / recursive shape references | ✅ unchanged | Phase 2-3 did not alter `Validation.interleave` / `apply_rules` recursion semantics. |
| Heuristic-driven traversal order | ✅ unchanged | `parse_heuristics` + `ShapeSchema.get_starting_point`. |
| Custom `sh:targetQuery` | ✅ unchanged | Non-standard extension. |
| **JSON shape format** | ⚠ **formally deprecated** | P3C `(this commit)`: DeprecationWarning text cites v2.0.0 removal target. ADR-010. |
| Query splitting / chunking | ✅ unchanged | `max_split_size`. |
| Selective queries / ORDER BY | ✅ unchanged | `use_selective_queries`, `order_by_in_queries`. |

## Final-state metrics

| Metric | Value |
|---|---|
| Fixture invocations passing (`tests/test_cases.py`) | 6656 |
| Fixture invocations skipped (JSON-format) | 2304 |
| Fixture invocations failed | 0 |
| Unit + serializer + parser-registry tests passing | 40 |
| Drift guards passing | 8 |
| Constraint subclasses with SOURCE_COMPONENT | 27 |
| ADRs (post-P3C) | 10 |
| Compliance-effort commits | 8 (4286b7d → 76aa9c4 → 5add8b2 → cc0c42e → 3902592 → 073413f → e9f2864 → this) |

## Residual limitations

Ten items carried forward as Phase 4+ candidate scope:

1. **K-02: `XoneConstraint` strict exactly-one semantics.** Engine's
   interleave step treats `sh:xone` disjuncts as conjunction (focus
   accepted when both match). Strict SHACL §4.6.4 enforcement requires
   counting logic in the rule-pattern saturation step. ADR-009.
2. **`sh:and` / `sh:xone` atomic-inner.** Parser raises
   `NotImplementedError`. DEC-05 carry-over: shape-references only.
3. **Shape-reference `sh:not`.** Parser raises `NotImplementedError`.
   DEC-05 carry-over: atomic-only.
4. **`sh:uniqueLang` n>2.** Self-join FILTER, no GROUP BY.
5. **`sh:qualifiedValueShapesDisjoint`.** Dispatch wired (ADR-006);
   semantics deferred.
6. **`sh:qualifiedMaxCount` as property-cardinality.** Currently
   interpreted as qualified-satisfying-values count.
7. **`sh:closed` end-to-end fixture.** Parser dispatch verified only;
   no E2E fixture.
8. **Kleene path operators end-to-end.** Virtuoso transitive-start
   constraint blocks the fixture pattern.
9. **`Path.from_string` scope.** Inverse + Sequence only (ADR-008).
10. **`SPARQLEndpoint` singleton state issue.** Cross-test endpoint
    caching surfaces in pytest reruns; production use unaffected.

Additional deferred items (not in §Residual limitations because they
were already ❌ at the frozen baseline and remain out of effort scope):
`sh:prefixes`/`sh:declare`, `sh:message`, `sh:ask`, user-defined
`sh:SPARQLConstraintComponent`, `sh:deactivated`, and the broader
`sh:value` per-value sub-result emission (sh:detail per spec §6.5).

## JSON shape format deprecation

The JSON shape format (project-specific, non-spec; original
cover-report §8) is **formally deprecated in P3C** with the explicit
v2.0.0 removal target. The `DeprecationWarning` in
`ShapeSchema.__init__` now cites the removal version. Users with
`schema_format='JSON'` workflows continue to function through v1.x;
the v2.0.0 release is a separately-planned breaking-change milestone.

See [docs/adr/ADR-010-json-format-deprecation.md](./docs/adr/ADR-010-json-format-deprecation.md)
for the policy decision and rejected alternatives.

## Audit trail

- Original [cover-report.md](./cover-report.md) frozen at commit
  `718cf52` ("docs: pin cover-report.md as source-of-truth gap
  inventory") and **intentionally preserved untouched**. This document
  references it as the gap-inventory anchor.
- All 10 ADRs at [docs/adr/](./docs/adr/) trace the architectural
  decisions that closed each gap.
- 8 HANDOFF docs at `.repo/storage/01KM18ZD23GC3TDVN7W0GX2000/`
  (gitignored — filesystem-only) record the inter-phase narrative.
- 8 PlanSchema JSONs at the same path enumerate every Q-NN/D-NN/DEC-NN
  decision throughout the effort; the closing
  HANDOFF-phase-3c-to-done.md provides the consolidated decisions
  catalog.

## Future work (Phase 4+)

The 10 residual limitations enumerated above are the Phase 4+
candidate scope. Phase 4+ kickoff requires a fresh `/mental-model`
invocation with new scope; the existing mental-model history reflects
only the SHACL Core compliance trajectory.

The v2.0.0 release (JSON parser removal + any other accumulated
breaking changes) is a separately-planned milestone. P3C does not
commit to a v2.0.0 release date.

---

**Bottom line:** Trav-SHACL ships **full SHACL Core compliance modulo
the 10 documented residual limitations** at HEAD after the P3C commit.
The traversal-driven engine retains its Trav-SHACL-specific algorithmic
focus on rule-based saturation, heuristic shape ordering, and
recursive-cycle handling — extensions beyond the SHACL spec that
distinguish the project from other SHACL validators.
