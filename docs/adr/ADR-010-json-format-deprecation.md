---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "Claude Opus 4.7 (1M context) via Claude Code"
  date: "2026-05-17"
---

# ADR-010: JSON Shape Format Formal Deprecation

## Status

Accepted for Phase 3C.

## Context

Trav-SHACL has historically accepted two shape-schema formats:

- **SHACL Turtle (.ttl)** — the spec-conformant format produced by every
  standard SHACL tool.
- **JSON** — a project-specific schema (`targetDef` / `constraintDef` /
  `prefix` keys) introduced as an alternative ingestion path. Listed in
  the original `cover-report.md` §8 "Non-standard extensions" as a
  Trav-SHACL-specific feature.

The JSON ingestion path has emitted a `DeprecationWarning` since Phase
2A (`TravSHACL/core/ShapeSchema.py` L57-62 at HEAD prior to P3C):

```
"The JSON format for shape schemas is deprecated and will be removed
 in a future version."
```

The message has been generic — "in a future version" — providing no
actionable upgrade target.

**Gap-divergence problem.** Phase 2B added 15 new constraint subclasses
(class/nodeKind, range, string, pair). Phase 2C added 7 more (logical,
qualified, closed, hasValue, in). Phase 2C-A added `XoneConstraint`.
Phase 3A added the `SOURCE_COMPONENT` polymorphic accessor on all 27
concrete subclasses. Phase 3B fixed the AndConstraint/XoneConstraint
engine saturation bug.

Every Turtle-only feature added across P2B/P2C/P2C-A/P3A/P3B would
require parallel JSON parser work to maintain format parity. The
project's `tests/test_cases.py` parametrize matrix has accumulated 2304
JSON-format skip clauses (as of HEAD `e9f2864`) — every Turtle-only
fixture skips the JSON arm of the matrix because the JSON parser
cannot represent the new constraints. Maintaining parity would
multiply the surface area of the parser without spec backing.

Phase 3's mental-model checkpoint (HEAD `3902592`, refreshed at
`mental-model.2026-05-17T11:45:19`) raised this explicitly as Q-18:
**extend, formally deprecate, or hard-remove?** Q-18 was LOCKED for
P3C at HEAD `073413f` per the P3A handoff; the P3B handoff
(HEAD `e9f2864`, §Part A) elaborated the deprecation policy.

This ADR records the decision.

## Decision

**Formal deprecation with explicit v2.0.0 removal target.**

The `DeprecationWarning` text in `ShapeSchema.__init__` is enhanced to
cite the removal version:

```
"The JSON format for shape schemas is deprecated and will be removed
 in v2.0.0. See docs/adr/ADR-010-json-format-deprecation.md for the
 deprecation policy."
```

The JSON parser code stays functional through the v1.x release line
and is removed in v2.0.0 as a separately-planned breaking-change
milestone.

The 2304 JSON-format skips in `tests/test_cases.py` remain in place as
documentary status, not failures — they record that each affected
fixture is Turtle-only, not that the JSON parser is broken.

## Alternatives Rejected

### (a) Hard removal in v1.x

Remove the JSON parser entirely in the next minor release. **Rejected**
because:

- Breaking for any user passing `schema_format='JSON'` to `ShapeSchema`.
- The Trav-SHACL `__init__` API surface advertises the kwarg as a
  documented integration point; removing it mid-minor violates semver.
- The cumulative cost of carrying the JSON parser through v1.x is low
  (no new code, just skip-pinned fixtures).

### (b) `strict_no_json=True` kwarg

Add a public kwarg that hard-fails on JSON ingestion. **Rejected**
because:

- Adds API surface for an ephemeral use case: users who want
  strict-no-JSON behavior can wrap `ShapeSchema` themselves or trap the
  DeprecationWarning as an error via `warnings.filterwarnings`.
- The v2.0.0 removal will replace the flag anyway; introducing it now
  creates a deprecate-then-remove cycle for a single kwarg.

### (c) JSON-format parity extension

Backport every Turtle-only constraint to the JSON parser so the matrix
runs both arms. **Rejected** because:

- Cumulative gap-divergence cost: ~20 constraints across P2B/P2C/P2C-A
  would need JSON parser additions; each adds maintenance load with no
  spec backing.
- The JSON format is project-specific (cover-report.md §8); there is
  no external standard to anchor parity decisions when the SHACL spec
  evolves.
- Investment compounds rather than amortizes: each future Trav-SHACL
  constraint extension would require the parallel JSON work.

## Consequences

### Resolved

- **DeprecationWarning text now actionable.** Users see `v2.0.0` as the
  explicit removal target and a pointer to this ADR.
- **Fixture-skip clarity.** The 2304 `tests/test_cases.py` skips have
  documentary status: each skip records that the fixture is Turtle-only
  by design.
- **API stability through v1.x.** Users with `schema_format='JSON'`
  workflows get advance notice without forced migration.

### Future

- **v2.0.0 release** is a separately-planned breaking-change milestone.
  Scope includes JSON parser removal and any other accumulated breaking
  changes the operator chooses to bundle. P3C does not commit to a v2.0.0
  release date.
- **Phase 4+ candidate scope** is enumerated in `cover-report-phase-3.md`
  §Residual limitations and `HANDOFF-phase-3c-to-done.md` §Go-forward —
  the 10 deferred items are independent of the JSON deprecation
  trajectory.

### Carry-overs (unchanged)

- **DEC-04** polymorphic dispatch invariant: JSON ingestion stays inside
  `ShapeParser`'s existing path; no engine/emitter changes.
- **Q-02** semantic distinction: JSON parser errors continue to raise
  `NotImplementedError` for unsupported constraints (atomic-only sh:and,
  shape-ref sh:not, etc.) — the deprecation does not change error
  semantics.

## References

- [ADR-001: Full-IRI Parser Dispatch Registry](ADR-001-parser-dispatch-registry.md) —
  records the parser-dispatch registry that the JSON ingestion path
  uses; v2.0.0 removal will simplify this registry by dropping the JSON
  branch.
- [cover-report.md](../../cover-report.md) §8 "Non-standard extensions" —
  identifies the JSON shape format as a Trav-SHACL-specific feature
  outside the SHACL spec.
- [HANDOFF-phase-3a-to-3b.md](../../.repo/storage/01KM18ZD23GC3TDVN7W0GX2000/HANDOFF-phase-3a-to-3b.md) —
  Q-18 LOCKED for P3C (formal deprecation, not hard removal).
- [HANDOFF-phase-3b-to-3c.md](../../.repo/storage/01KM18ZD23GC3TDVN7W0GX2000/HANDOFF-phase-3b-to-3c.md) §Part A —
  elaborates the P3C deprecation scope and rejects parity extension.
- [cover-report-phase-3.md](../../cover-report-phase-3.md) — the final
  compliance status document; references this ADR in §JSON deprecation.
- [plan-phase-3c.latest.json](../../.repo/storage/01KM18ZD23GC3TDVN7W0GX2000/plan-phase-3c.latest.json) —
  the P3C execution plan that delivers this ADR.
