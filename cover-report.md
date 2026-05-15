---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "Claude Opus 4.7 (1M context) via Claude Code"
  date: "2026-05-15"
---

# Trav-SHACL — SHACL Spec Coverage Matrix

Verdicts below are derived structurally from `TravSHACL/core/ShapeParser.py` (the only place that maps SHACL vocabulary into the engine's internal model), the constraint class hierarchy under `TravSHACL/constraints/`, the SPARQL queries the parser issues against an `sh:NodeShape` graph, and the `tests/cases/**` fixtures that exercise each feature. They are independent of the project's own README/docs.

## Method (how this was determined)

- **Parser truth table** — `parse_all_const` (`ShapeParser.py:368-445`) only writes into a fixed-key dict: `min`, `max`, `value`, `path`, `shape`, `datatype`, `negated`, `or`, `flag`, `sparql`. Any SHACL property whose local name does not lowercase-match `'min'`, `'max'`, `'path'`, `'datatype'`, `'valueshape'`, `'not'`, or land in the `sh:or`/`sh:sparql` SPARQL probes (`get_QUERY:241-309`) is silently dropped (or raises `NotImplementedError` if `ignore_errors=False`, see `get_res:311-366`).
- **TTL probe set** — the parser issues exactly these SHACL-vocabulary queries: `sh:NodeShape`, `sh:targetClass`, `sh:targetNode`, `sh:targetQuery`, `sh:property`, `sh:path` (with `sh:inversePath` and `rdf:rest*/rdf:first` list-walking branches), `sh:node`, `sh:value`, `sh:sparql/sh:select`, `sh:or`. That is the complete set of SHACL IRIs the engine knows.
- **Constraint classes** — only 4 concrete subclasses of `Constraint`: `MinOnlyConstraint`, `MaxOnlyConstraint`, `MinMaxConstraint`, `SPARQLConstraint`. Each holds `(min, max, path, datatype, value, shape_ref, is_pos, options)`. No other constraint types exist.
- **Fixture taxonomy** — directories under `tests/cases/`: `single_shape`, `two_shapes`, `inverse_path`, `or_constraint`, `recursion`, `sparql_constraint`. No fixture exists for class-pair, pattern, language, list, qualified-value-shape min/max, logical NOT/AND/XONE, etc.

## 1. Targets (SHACL §2.1)

| Spec feature | IRI | Support | Evidence |
|---|---|---|---|
| Class target | `sh:targetClass` | ✅ | `QUERY_TARGET_1` in `get_QUERY:241-309`; `target_type = 'class'` |
| Node target | `sh:targetNode` | ✅ | `QUERY_TARGET_2` (same block); `target_type = 'node'` |
| Custom SPARQL target | `sh:targetQuery` | ✅ (non-standard extension) | `QUERY_TARGET_QUERY` literal at top of `ShapeParser.py`; also `targetDef.query` in JSON |
| Subjects-of target | `sh:targetSubjectsOf` | ❌ | No probe issued |
| Objects-of target | `sh:targetObjectsOf` | ❌ | No probe issued |
| Implicit class target (`rdfs:Class` + NodeShape) | implicit | ❌ | Only `sh:NodeShape` is queried as the shape selector |

## 2. Shape types (SHACL §2.2)

| Spec feature | Support | Evidence |
|---|---|---|
| `sh:NodeShape` (top-level) | ✅ | `QUERY_SHAPES` selects only `?shape a sh:NodeShape` |
| `sh:PropertyShape` (top-level) | ❌ | Never enumerated; the parser walks `sh:property` blank nodes hanging off a NodeShape but does not treat property shapes as first-class targets |
| Inline blank-node shapes via `sh:property` | ⚠ Partial | Walked, but only the recognized predicates inside are kept |
| Nested `sh:node` reference | ✅ | `QUERY_QVS_REF_1` (`sh:node`) — produces `shape_ref` |
| `sh:and` | ❌ | No probe; conjunction is implicit (all properties on a NodeShape are AND'd, but explicit `sh:and` lists are not parsed) |
| `sh:or` | ✅ (NodeShape-level) | `QUERY_OR` + the `dk == "Graph.items"` branch in `parse_all_const` |
| `sh:xone` | ❌ | No probe |
| `sh:not` | ⚠ Partial via `negated` flag | `'not' in str(i[0]).lower()` in `parse_all_const`; surfaces as `is_pos=False` on min/max constraints. No first-class negation operator — only inversion of cardinality constraints. |

## 3. Property paths (SHACL §2.3)

| Path expression | IRI | Support | Evidence |
|---|---|---|---|
| Predicate (atomic) | IRI | ✅ | Default branch in `QUERY_CONSTRAINT_DETAILS` |
| Inverse path | `sh:inversePath` | ✅ | Dedicated UNION branch: `?s sh:path/sh:inversePath ?o … BIND(CONCAT('^', str(?o)) AS ?o)` — fixtures: `tests/cases/inverse_path/case{1,2}` |
| Sequence path | RDF list of paths | ⚠ Partial | The third UNION branch walks `rdf:rest*/rdf:first` and `group_concat`s with `/` separator. Works for lists of plain IRIs only; nested inverse/alternative paths in a list are not handled. |
| Alternative path | `sh:alternativePath` | ❌ | No probe; would land in the unsupported feature branch of `get_res` |
| Zero-or-more path | `sh:zeroOrMorePath` | ❌ | Not recognized |
| One-or-more path | `sh:oneOrMorePath` | ❌ | Not recognized |
| Zero-or-one path | `sh:zeroOrOnePath` | ❌ | Not recognized |

## 4. Core constraint components (SHACL §4)

### 4.1 Cardinality

| Constraint | IRI | Support | Evidence |
|---|---|---|---|
| Min count | `sh:minCount` | ✅ | `'min' in str(i[0]).lower()` → `MinOnlyConstraint` / `MinMaxConstraint` |
| Max count | `sh:maxCount` | ✅ | `'max' in str(i[0]).lower()` → `MaxOnlyConstraint` / `MinMaxConstraint` |

### 4.2 Value-type constraints

| Constraint | IRI | Support | Evidence |
|---|---|---|---|
| Datatype | `sh:datatype` | ⚠ Stored, partially enforced | `'datatype' in str(i[0]).lower()`; stored on `Constraint.datatype` and surfaced as a filter in `QueryBuilder.add_datatype_filter`. Only filters in the generated SPARQL; no separate `DatatypeConstraint` class. |
| Node kind | `sh:nodeKind` | ❌ | Not in the recognized-keys table |
| Class | `sh:class` | ❌ | Not in the table — only `sh:targetClass` (a target, not a value constraint) |

### 4.3 Value-range constraints

| Constraint | IRI | Support | Evidence |
|---|---|---|---|
| `sh:minInclusive` / `sh:maxInclusive` | — | ❌ | Substring `'min'`/`'max'` actually matches these property local names too, but the parser treats them as cardinality counts (writes into `trav_dict['min']` / `['max']`) and feeds them to a `MinOnly`/`MaxOnly`/`MinMaxConstraint`. **This is a latent bug**: a shape with `sh:minInclusive 18` would be parsed as `sh:minCount 18`. |
| `sh:minExclusive` / `sh:maxExclusive` | — | ❌ | Same latent collision |

### 4.4 String-based constraints

| Constraint | IRI | Support |
|---|---|---|
| `sh:minLength` / `sh:maxLength` | — | ❌ (collides with cardinality keys — same bug) |
| `sh:pattern` | — | ❌ |
| `sh:languageIn` | — | ❌ |
| `sh:uniqueLang` | — | ❌ |

### 4.5 Property-pair constraints

| Constraint | IRI | Support |
|---|---|---|
| `sh:equals` | — | ❌ |
| `sh:disjoint` | — | ❌ |
| `sh:lessThan` | — | ❌ |
| `sh:lessThanOrEquals` | — | ❌ |

### 4.6 Logical constraints

| Constraint | IRI | Support |
|---|---|---|
| `sh:and` | — | ❌ (implicit conjunction only) |
| `sh:or` | — | ✅ (NodeShape level, via `QUERY_OR`) |
| `sh:not` | — | ⚠ Polarity flip only (`negated` key); cannot negate arbitrary shapes |
| `sh:xone` | — | ❌ |

### 4.7 Shape-based constraints

| Constraint | IRI | Support | Evidence |
|---|---|---|---|
| `sh:node` | — | ✅ | `QUERY_QVS_REF_1` — produces a `shape_ref` (used to build the shape-dependency graph) |
| `sh:property` | — | ✅ | `QUERY_CONSTRAINTS` |
| `sh:qualifiedValueShape` | — | ❌ | Not recognized |
| `sh:qualifiedMinCount` / `sh:qualifiedMaxCount` | — | ❌ | Lexical-substring collision with `sh:minCount`/`sh:maxCount` — same bug as 4.3 |
| `sh:qualifiedValueShapesDisjoint` | — | ❌ | |

### 4.8 Other

| Constraint | IRI | Support |
|---|---|---|
| `sh:closed` + `sh:ignoredProperties` | — | ❌ |
| `sh:hasValue` | — | ⚠ `'valueshape' in str(i[0]).lower()` catches `sh:value` indirectly through the QVS-ref path; direct `sh:hasValue` is not in the table. Result: stored, but enforcement path is murky. |
| `sh:in` (enumerated values) | — | ❌ |

## 5. SPARQL-based constraints (SHACL §5)

| Spec feature | IRI | Support | Evidence |
|---|---|---|---|
| `sh:sparql` + `sh:SPARQLConstraint` + `sh:select` | — | ✅ | `QUERY_SPARQL_CONSTRAINTS` in `ShapeParser.get_QUERY` → `SPARQLConstraint`. Fixtures: `tests/cases/sparql_constraint/case{1,2,3}` |
| `sh:prefixes` / `sh:declare` (prefix declarations for SPARQL) | — | ❌ | Not parsed — user must inline full IRIs in `sh:select` |
| `sh:message` (custom violation messages) | — | ❌ | Not extracted |
| `sh:ask` constraints | — | ❌ | Only `sh:select` is probed |
| `sh:SPARQLConstraintComponent` (user-defined components) | — | ❌ | No parameter-binding machinery |

## 6. Validation reports (SHACL §3)

| Spec feature | IRI | Support |
|---|---|---|
| `sh:ValidationReport` | — | ❌ |
| `sh:ValidationResult` | — | ❌ |
| `sh:conforms` boolean | — | ❌ |
| `sh:resultSeverity` (Violation/Warning/Info) | — | ❌ |
| `sh:focusNode`, `sh:resultPath`, `sh:value`, `sh:sourceShape`, `sh:sourceConstraintComponent` | — | ❌ |
| `sh:resultMessage` | — | ❌ |

Trav-SHACL emits its own report shape: per-target labels (`valid_*` / `violated_*`) written by `Validation.validation_output` via `utils/fileManagement.py`. **It is not a SHACL-conformant report.**

## 7. Severity, deactivation, metadata

| Spec feature | IRI | Support |
|---|---|---|
| `sh:severity` | — | ❌ |
| `sh:deactivated` | — | ❌ |
| `sh:name`, `sh:description`, `sh:group`, `sh:order`, `sh:defaultValue` | — | ❌ |

## 8. Beyond-spec extensions (what Trav-SHACL adds)

These are features the SHACL specification does not define but Trav-SHACL ships:

| Feature | Where |
|---|---|
| Cyclic / recursive shape references with rule-based fixpoint | `Validation.interleave` + `apply_rules`; fixtures `tests/cases/recursion/case{1,2,3,4}`. (SHACL Core leaves recursion undefined; SHACL-SPARQL forbids it.) |
| Heuristic-driven traversal order (BFS/DFS + target/in-degree/out-degree heuristics) | `utils/parse_heuristics` + `ShapeSchema.get_starting_point` |
| Custom `sh:targetQuery` | Bespoke predicate; mentioned in §1 |
| JSON shape format | `targetDef` / `constraintDef.conjunctions` / `prefix` schema in `.json` files; non-spec alternative to Turtle |
| Query splitting / chunking | `max_split_size`, `Shape.get_query_split_threshold` |
| Selective queries / `ORDER BY` | `use_selective_queries`, `order_by_in_queries` parameters of `ShapeSchema` |

## 9. Summary verdict

**Implemented (core spec):** `sh:NodeShape`, `sh:targetClass`, `sh:targetNode`, `sh:property`, `sh:path` (atomic, inverse, simple sequence), `sh:minCount`, `sh:maxCount`, `sh:datatype` (filter only), `sh:node`, `sh:or` (NodeShape level), `sh:sparql`/`sh:select`, an `is_pos` flip when `sh:not` is lexically present.

**Missing or unsafe:**

- All non-cardinality numeric / string / language / pattern constraints (4.3–4.4).
- All property-pair constraints (4.5).
- `sh:and`, `sh:xone`, full `sh:not` (4.6).
- All qualified-value-shape constraints (4.7).
- `sh:closed`, `sh:hasValue` (direct), `sh:in`.
- `sh:targetSubjectsOf`, `sh:targetObjectsOf`, implicit class targets.
- Most path expressions: `sh:alternativePath`, `sh:zeroOrMore`, `sh:oneOrMore`, `sh:zeroOrOne`.
- Severity / messages / deactivation / metadata.
- Standard validation report serialization.
- `sh:prefixes`/`sh:declare` for SPARQL constraints; `sh:ask`; user-defined `sh:SPARQLConstraintComponent`.

**Latent correctness risk:** the parser dispatch is lexical-substring on lowercased local names in `parse_all_const` (`ShapeParser.py:368-445`). This means:

- `sh:minInclusive`, `sh:minExclusive`, `sh:minLength`, `sh:qualifiedMinCount` all collide with `'min'` → silently interpreted as `sh:minCount`.
- Same for the `'max'` family.
- `sh:hasValue` does not collide with the recognized `'valueshape'` key, so it is dropped or raises `NotImplementedError` (depending on `ignore_errors`).

**Bottom line:** Trav-SHACL implements a deliberately narrow slice of SHACL Core — cardinality + shape-references + raw-SPARQL escape hatch — and is built around algorithmic contributions (traversal-order heuristics and rule-based recursion semantics) rather than spec completeness. For a validator targeting full spec compliance, prefer `pyshacl` or Apache Jena SHACL; for shape-graph-aware federation/traversal experiments on a SPARQL endpoint, Trav-SHACL fills a niche the spec-conformant tools do not.
