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

- **Parser truth table** — `CONSTRAINT_DISPATCH` in `TravSHACL/core/ShapeParser.py` now maps exact SHACL IRIs into fixed internal keys. Unknown SHACL predicates raise `NotImplementedError` unless `ignore_errors=True`.
- **TTL probe set** — the parser enumerates node and property shapes, target forms, property constraints, shape-level logical/closed constraints, SPARQL constraints, and RDF-structured path expressions through `parse_path_node`.
- **Constraint classes** — the hierarchy now includes dedicated classes for value-type, value-range, string, property-pair, qualified value shape, direct value, closed, and selected logical constraints. Query emission remains polymorphic through `Constraint.emit_filter`.
- **Fixture taxonomy** — regression coverage includes parser/AST/drift tests plus the existing full fixture matrix. Local RDFLib graph validation passed for the non-HTTP axis on 2026-05-15.

## 1. Targets (SHACL §2.1)

| Spec feature | IRI | Support | Evidence |
|---|---|---|---|
| Class target | `sh:targetClass` | ✅ | `QUERY_TARGET_1` in `get_QUERY:241-309`; `target_type = 'class'` |
| Node target | `sh:targetNode` | ✅ | `QUERY_TARGET_2` (same block); `target_type = 'node'` |
| Custom SPARQL target | `sh:targetQuery` | ✅ (non-standard extension) | `QUERY_TARGET_QUERY` literal at top of `ShapeParser.py`; also `targetDef.query` in JSON |
| Subjects-of target | `sh:targetSubjectsOf` | ✅ | `QUERY_TARGET_SUBJECTS_OF`; fixtures: `tests/cases/target_subjects_of/` |
| Objects-of target | `sh:targetObjectsOf` | ✅ | `QUERY_TARGET_OBJECTS_OF`; fixtures: `tests/cases/target_objects_of/` |
| Implicit class target (`rdfs:Class` + NodeShape) | implicit | ✅ | `QUERY_IMPLICIT_CLASS`; fixtures: `tests/cases/implicit_class/` |

## 2. Shape types (SHACL §2.2)

| Spec feature | Support | Evidence |
|---|---|---|
| `sh:NodeShape` (top-level) | ✅ | `QUERY_SHAPES` selects only `?shape a sh:NodeShape` |
| `sh:PropertyShape` (top-level) | ✅ | `QUERY_SHAPES` selects NodeShape and PropertyShape entries; fixtures: `tests/cases/property_shape/` |
| Inline blank-node shapes via `sh:property` | ⚠ Partial | Walked, but only the recognized predicates inside are kept |
| Nested `sh:node` reference | ✅ | `QUERY_QVS_REF_1` (`sh:node`) — produces `shape_ref` |
| `sh:and` | ✅ subset | Shape-reference lists compile to `AndConstraint`; nested arbitrary shape expressions remain limited |
| `sh:or` | ✅ (NodeShape-level) | `QUERY_OR` + the `dk == "Graph.items"` branch in `parse_all_const` |
| `sh:xone` | ❌ | Recognized by dispatch but raises `NotImplementedError` to avoid silently behaving like `sh:and` |
| `sh:not` | ✅ subset | Atomic property-shape negation compiles to `NotConstraint`; shape-reference `sh:not` fails fast with `NotImplementedError` |

## 3. Property paths (SHACL §2.3)

| Path expression | IRI | Support | Evidence |
|---|---|---|---|
| Predicate (atomic) | IRI | ✅ | Default branch in `QUERY_CONSTRAINT_DETAILS` |
| Inverse path | `sh:inversePath` | ✅ | Dedicated UNION branch: `?s sh:path/sh:inversePath ?o … BIND(CONCAT('^', str(?o)) AS ?o)` — fixtures: `tests/cases/inverse_path/case{1,2}` |
| Sequence path | RDF list of paths | ✅ | `parse_path_node` creates `Sequence` recursively |
| Alternative path | `sh:alternativePath` | ✅ | `parse_path_node` creates `Alternative` |
| Zero-or-more path | `sh:zeroOrMorePath` | ✅ | `parse_path_node` creates `ZeroOrMore` |
| One-or-more path | `sh:oneOrMorePath` | ✅ | `parse_path_node` creates `OneOrMore` |
| Zero-or-one path | `sh:zeroOrOnePath` | ✅ | `parse_path_node` creates `ZeroOrOne` |

## 4. Core constraint components (SHACL §4)

### 4.1 Cardinality

| Constraint | IRI | Support | Evidence |
|---|---|---|---|
| Min count | `sh:minCount` | ✅ | `'min' in str(i[0]).lower()` → `MinOnlyConstraint` / `MinMaxConstraint` |
| Max count | `sh:maxCount` | ✅ | `'max' in str(i[0]).lower()` → `MaxOnlyConstraint` / `MinMaxConstraint` |

### 4.2 Value-type constraints

| Constraint | IRI | Support | Evidence |
|---|---|---|---|
| Datatype | `sh:datatype` | ✅ | Exact dispatch key; enforced through datatype filters |
| Node kind | `sh:nodeKind` | ✅ | `NodeKindConstraint`; parser rejects unsupported node kinds |
| Class | `sh:class` | ✅ | `ClassConstraint` with subclass traversal |

### 4.3 Value-range constraints

| Constraint | IRI | Support | Evidence |
|---|---|---|---|
| `sh:minInclusive` / `sh:maxInclusive` | — | ✅ | `RangeMinInclusiveConstraint` / `RangeMaxInclusiveConstraint` |
| `sh:minExclusive` / `sh:maxExclusive` | — | ✅ | `RangeMinExclusiveConstraint` / `RangeMaxExclusiveConstraint` |

### 4.4 String-based constraints

| Constraint | IRI | Support |
|---|---|---|
| `sh:minLength` / `sh:maxLength` | — | ✅ |
| `sh:pattern` | — | ✅ |
| `sh:languageIn` | — | ✅ |
| `sh:uniqueLang` | — | ✅ |

### 4.5 Property-pair constraints

| Constraint | IRI | Support |
|---|---|---|
| `sh:equals` | — | ✅ |
| `sh:disjoint` | — | ✅ |
| `sh:lessThan` | — | ✅ |
| `sh:lessThanOrEquals` | — | ✅ |

### 4.6 Logical constraints

| Constraint | IRI | Support |
|---|---|---|
| `sh:and` | — | ✅ subset: shape-reference lists |
| `sh:or` | — | ✅ (NodeShape level, via `QUERY_OR`) |
| `sh:not` | — | ✅ subset: atomic property-shape negation; shape-reference negation is explicit `NotImplementedError` |
| `sh:xone` | — | ❌ fail-fast `NotImplementedError` |

### 4.7 Shape-based constraints

| Constraint | IRI | Support | Evidence |
|---|---|---|---|
| `sh:node` | — | ✅ | `QUERY_QVS_REF_1` — produces a `shape_ref` (used to build the shape-dependency graph) |
| `sh:property` | — | ✅ | `QUERY_CONSTRAINTS` |
| `sh:qualifiedValueShape` | — | ✅ | `QualifiedValueShapeConstraint` |
| `sh:qualifiedMinCount` / `sh:qualifiedMaxCount` | — | ✅ | Qualified min/max are dedicated parser keys, not aliases |
| `sh:qualifiedValueShapesDisjoint` | — | ⚠ Parsed | Key is recognized; disjoint-specific semantics are not separately enforced |

### 4.8 Other

| Constraint | IRI | Support |
|---|---|---|
| `sh:closed` + `sh:ignoredProperties` | — | ✅ |
| `sh:hasValue` | — | ✅ |
| `sh:in` (enumerated values) | — | ✅ |

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

**Implemented (core spec):** `sh:NodeShape`, `sh:PropertyShape`, core target forms, common property paths, cardinality, datatype, value-type, value-range, string, property-pair, qualified value-shape, closed, direct value, and selected logical constraints, plus `sh:sparql`/`sh:select`.

**Missing or unsafe:**

- `sh:xone`.
- Full nested shape-expression semantics for `sh:and`.
- Shape-reference `sh:not`.
- Dedicated `sh:qualifiedValueShapesDisjoint` behavior.
- Severity / messages / deactivation / metadata.
- Standard validation report serialization.
- `sh:prefixes`/`sh:declare` for SPARQL constraints; `sh:ask`; user-defined `sh:SPARQLConstraintComponent`.

**Latent correctness risk:** the remaining risks are no longer lexical dispatch collisions; they are semantic subset boundaries. The most important are shape-reference negation, full nested logical expression support, qualified-disjoint semantics, and SHACL-conformant validation report serialization.

**Bottom line:** Trav-SHACL now covers the main SHACL Core validation families used by its fixture suite while preserving its algorithmic focus on traversal-order heuristics and rule-based recursion semantics. Phase 3 should focus on standard report serialization and JSON-format parity for the newly added Turtle-only constraints.
