---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "GPT-5 Codex"
  date: "2026-05-15"
---

# Drift-Risk Map — Trav-SHACL

**Generated**: 2026-05-15T08:39:25-03:00
**Scope**: Full repo
**Commit / ref**: `eaf6e6e44728cadf28c13754d6860f40e89f493e`

## Executive Summary

10 couplings found. Original scan: 3 CRITICAL, 2 HIGH, 1 MODERATE, 4 LOW.
After remediation: 0 unguarded CRITICAL/P0 couplings remain; the three original
CRITICAL findings are guarded by [tests/test_drift_guards.py](/home/admin/github-mirror/_forks/Trav-SHACL/tests/test_drift_guards.py:1).
The two original HIGH/P1 couplings are also guarded by the same regression
test module.

**Top-3 originally critical drift vectors now guarded by regression tests:**

1. `ShapeSchema.__init__` is documented by hand in [docs/library.rst](/home/admin/github-mirror/_forks/Trav-SHACL/docs/library.rst:173). It is now guarded by `test_shape_schema_documented_parameters_match_constructor`, which compares the documented parameter inventory, required-parameter sentence, and example keyword arguments against the live constructor source.
2. The Flask service contract in [TravSHACL/app/__init__.py](/home/admin/github-mirror/_forks/Trav-SHACL/TravSHACL/app/__init__.py:11) and [Dockerfile](/home/admin/github-mirror/_forks/Trav-SHACL/Dockerfile:14) is manually mirrored across [example/docker-compose.yml](/home/admin/github-mirror/_forks/Trav-SHACL/example/docker-compose.yml:16) and [docs/service.rst](/home/admin/github-mirror/_forks/Trav-SHACL/docs/service.rst:60). It is now guarded by `test_service_docs_match_flask_docker_and_compose_contract`.
3. The runnable example topology in [example/docker-compose.yml](/home/admin/github-mirror/_forks/Trav-SHACL/example/docker-compose.yml:3) is restated in [docs/library.rst](/home/admin/github-mirror/_forks/Trav-SHACL/docs/library.rst:93), [docs/service.rst](/home/admin/github-mirror/_forks/Trav-SHACL/docs/service.rst:60), and [example/README.md](/home/admin/github-mirror/_forks/Trav-SHACL/example/README.md:9). It is now guarded by `test_example_docs_match_compose_topology`.

**Overall posture**: The core library surfaces are relatively disciplined where they reuse shared files directly: `VERSION`, `README.md`, `CHANGELOG.md`, and `CONTRIBUTORS.md` flow into packaging or Sphinx through imports rather than copy-paste. The fragile area is the repo perimeter: service mode, example topology, support promises, and feature claims are maintained manually in multiple places. That means the main silent-drift risk is not the validation engine itself; it is the surrounding human-facing contract layer that can go stale while the test suite still passes.

> A visual overview of this coupling topology is available in
> `drift-risk-map.svg` (generated alongside this report).

## Coupling Inventory

| # | Source Artifact | Dependent Artifact(s) | Coupling Mechanism | Consistency Guard | Propagation Mode | Drift Risk |
|---|---|---|---|---|---|---|
| 1 | `TravSHACL/core/ShapeSchema.py:20-44` | `docs/library.rst:117-195` | manual-mirror | `tests/test_drift_guards.py::test_shape_schema_documented_parameters_match_constructor` | test-failure | **LOW** |
| 2 | `TravSHACL/app/__init__.py:11-39`, `Dockerfile:14-17` | `example/docker-compose.yml:16-23`, `docs/service.rst:60-82` | manual-mirror | `tests/test_drift_guards.py::test_service_docs_match_flask_docker_and_compose_contract` | test-failure | **LOW** |
| 3 | `example/docker-compose.yml:3-31` | `docs/library.rst:93-102`, `docs/service.rst:60-82`, `example/README.md:9-25` | manual-mirror | `tests/test_drift_guards.py::test_example_docs_match_compose_topology` | test-failure | **LOW** |
| 4 | `setup.py:28-39` | `.github/workflows/test.yml:28-31` | manual-mirror | `tests/test_drift_guards.py::test_supported_python_versions_match_ci_matrix` | test-failure | **LOW** |
| 5 | `TravSHACL/core/ShapeSchema.py:20-44`, `TravSHACL/core/ShapeParser.py`, `tests/test_cases.py:19-68` | `docs/feature.rst:5-30` | manual-mirror | `tests/test_drift_guards.py::test_feature_claims_have_source_or_fixture_evidence` | test-failure | **LOW** |
| 6 | `tests/docker-compose.yml:3-10` | `tests/test_cases.py:11`, `.github/workflows/test.yml:34-41` | manual-mirror | `pytest` in CI plus endpoint wait step | test-failure | **MODERATE** |
| 7 | `VERSION:1` | `setup.py:4-5`, `docs/conf.py:18-26` | shared-import | package build and Sphinx build consume the same file | build-error | **LOW** |
| 8 | `README.md:15-53` | `setup.py:7,26`, `setup.cfg:3` | shared-import | package build reads README directly | build-error | **LOW** |
| 9 | `CHANGELOG.md:1-20` | `docs/changelog.rst:1-9` | shared-import | `mdinclude` during Sphinx build | build-error | **LOW** |
| 10 | `CONTRIBUTORS.md:1-14` | `docs/contributors.rst:1-10` | shared-import | `mdinclude` during Sphinx build | build-error | **LOW** |

### Coupling mechanism legend

- **codegen**: Dependent is machine-generated from the source. Stays in sync if the generation step runs.
- **shared-import**: Dependent imports types/values directly from the source module. Compiler/interpreter enforces the contract.
- **manual-mirror**: Dependent restates information from the source by hand. No automated enforcement.
- **contract-test**: A dedicated test asserts agreement between source and dependent.
- **lint-rule**: A linter or static analysis rule enforces consistency.
- **build-step**: A build/compile step fails if the artifacts disagree.
- **runtime-validation**: Inconsistency is caught at runtime, not at build/test time.
- **none**: No known enforcement mechanism.

### Propagation mode legend

- **build-error**: Change in source causes a build/compile failure.
- **type-error**: Change causes a type-checker failure.
- **test-failure**: Change causes an existing test to fail.
- **lint-failure**: Change causes a linter to flag.
- **runtime-error**: Change causes an error at runtime.
- **silent**: Change propagates with no error; the dependent artifact is now wrong.

## Remediated CRITICAL Findings

### Finding #1: `ShapeSchema` public API is mirrored into library docs by hand

**Source**: [TravSHACL/core/ShapeSchema.py:20](/home/admin/github-mirror/_forks/Trav-SHACL/TravSHACL/core/ShapeSchema.py:20) — the keyword-only constructor defines the public library interface.
**Dependent**: [docs/library.rst:117](/home/admin/github-mirror/_forks/Trav-SHACL/docs/library.rst:117), [docs/library.rst:173](/home/admin/github-mirror/_forks/Trav-SHACL/docs/library.rst:173) — examples and parameter inventory restate that interface manually.
**Mechanism**: manual-mirror
**Guard**: [tests/test_drift_guards.py](/home/admin/github-mirror/_forks/Trav-SHACL/tests/test_drift_guards.py:1) asserts doc/signature parity for the parameter list, required-parameter sentence, and example keyword arguments.

**How drift manifests**: If a developer adds, removes, renames, or changes the semantics of a `ShapeSchema` argument, the docs can silently remain wrong. The package still builds, and the tests in [tests/test_cases.py](/home/admin/github-mirror/_forks/Trav-SHACL/tests/test_cases.py:19) can keep passing because they do not assert doc parity. Users then copy examples or parameter descriptions from the docs and get behavior that no longer matches the code.

**Implemented fix**: Added `test_shape_schema_documented_parameters_match_constructor`, a static pytest guard that fails if `ShapeSchema.__init__` and the manually maintained library docs drift.

---

### Finding #2: Service runtime contract is mirrored across app code, Docker, compose, and docs

**Source**: [TravSHACL/app/__init__.py:11](/home/admin/github-mirror/_forks/Trav-SHACL/TravSHACL/app/__init__.py:11) and [Dockerfile:14](/home/admin/github-mirror/_forks/Trav-SHACL/Dockerfile:14) — the Flask app defines `/validate`, runtime env keys, and listens on port `5000`.
**Dependent**: [example/docker-compose.yml:16](/home/admin/github-mirror/_forks/Trav-SHACL/example/docker-compose.yml:16) and [docs/service.rst:76](/home/admin/github-mirror/_forks/Trav-SHACL/docs/service.rst:76) — external port mapping, endpoint URL, and UI instructions depend on those values.
**Mechanism**: manual-mirror
**Guard**: [tests/test_drift_guards.py](/home/admin/github-mirror/_forks/Trav-SHACL/tests/test_drift_guards.py:1) asserts that the documented service URL, internal endpoint, container names, mounted shape path, Flask route, Docker port, and compose port mapping agree.

**How drift manifests**: If the app route changes from `/validate`, if the container port changes from `5000`, or if the required env keys evolve, the compose example and service docs will quietly lie. Nothing in CI currently boots the example engine and confirms that `http://localhost:9091/validate` serves the documented form.

**Implemented fix**: Added `test_service_docs_match_flask_docker_and_compose_contract`, a static pytest guard that catches route, port, container-name, endpoint, and mount-path drift without requiring Docker startup.

---

### Finding #3: Example topology is restated in three human-facing docs with no executable proof

**Source**: [example/docker-compose.yml:3](/home/admin/github-mirror/_forks/Trav-SHACL/example/docker-compose.yml:3) — service names, ports, image names, and mounted paths define the runnable example.
**Dependent**: [docs/library.rst:93](/home/admin/github-mirror/_forks/Trav-SHACL/docs/library.rst:93), [docs/service.rst:60](/home/admin/github-mirror/_forks/Trav-SHACL/docs/service.rst:60), and [example/README.md:9](/home/admin/github-mirror/_forks/Trav-SHACL/example/README.md:9) — commands and URLs are all hand-maintained copies.
**Mechanism**: manual-mirror
**Guard**: [tests/test_drift_guards.py](/home/admin/github-mirror/_forks/Trav-SHACL/tests/test_drift_guards.py:1) asserts the documented compose commands and external URLs match `example/docker-compose.yml`.

**How drift manifests**: A port change, container rename, mount-path change, or image name change in the compose file can leave one or more docs stale while CI stays green. The docs still render, and the package tests never notice because they do not execute the example stack.

**Implemented fix**: Added `test_example_docs_match_compose_topology`, a doc-example verifier that parses `example/docker-compose.yml` and asserts the documented command and URL surface remains synchronized.

## Remediated HIGH Findings

### Finding #4: Supported Python versions are declared in one place and tested in another

**Source**: [setup.py:29](/home/admin/github-mirror/_forks/Trav-SHACL/setup.py:29) — packaging metadata declares `python_requires` and per-version classifiers.
**Dependent**: [.github/workflows/test.yml:28](/home/admin/github-mirror/_forks/Trav-SHACL/.github/workflows/test.yml:28) — CI matrix names the supported interpreters separately.
**Mechanism**: manual-mirror
**Guard**: [tests/test_drift_guards.py](/home/admin/github-mirror/_forks/Trav-SHACL/tests/test_drift_guards.py:1) asserts that package classifiers, `python_requires`, and the GitHub Actions Python matrix agree.

**Implemented fix**: Aligned `python_requires` with the tested/classified floor (`>=3.9`) and added `test_supported_python_versions_match_ci_matrix`, which fails if package support metadata and the CI matrix diverge.

---

### Finding #5: Feature-support claims are still a human-maintained contract layer

**Source**: the live capability surface in [TravSHACL/core/ShapeSchema.py](/home/admin/github-mirror/_forks/Trav-SHACL/TravSHACL/core/ShapeSchema.py:20), [TravSHACL/core/ShapeParser.py](/home/admin/github-mirror/_forks/Trav-SHACL/TravSHACL/core/ShapeParser.py:20), and the exercised fixtures in [tests/test_cases.py](/home/admin/github-mirror/_forks/Trav-SHACL/tests/test_cases.py:19).
**Dependent**: [docs/feature.rst:5](/home/admin/github-mirror/_forks/Trav-SHACL/docs/feature.rst:5) — the feature matrix is prose, not a generated capability table.
**Mechanism**: manual-mirror
**Guard**: [tests/test_drift_guards.py](/home/admin/github-mirror/_forks/Trav-SHACL/tests/test_drift_guards.py:1) ties supported feature claims to fixture or source evidence.

**Implemented fix**: Added `test_feature_claims_have_source_or_fixture_evidence`, which checks the documented claims for cardinality, datatype, qualified-shape constraints, SPARQL constraints, `sh:or`, inverse paths, private SPARQL endpoints, and RDFLib graphs against fixture or source evidence.

## Methodology Notes

### What was inspected

- Root packaging and runtime files: `README.md`, `setup.py`, `setup.cfg`, `VERSION`, `requirements*.txt`, `Dockerfile`
- Python runtime entrypoints: `main.py`, `TravSHACL/TravSHACL.py`, `TravSHACL/app/__init__.py`, `TravSHACL/core/ShapeSchema.py`
- Sphinx/doc build layer: `docs/conf.py`, `docs/Makefile`, `docs/deploy.sh`, `docs/library.rst`, `docs/service.rst`, `docs/feature.rst`, `docs/changelog.rst`, `docs/contributors.rst`, `docs/README.md`
- Example and test harness infrastructure: `example/docker-compose.yml`, `example/README.md`, `tests/docker-compose.yml`, `tests/test_cases.py`, `tests/cases/**/definitions/*.json`
- CI workflows: `.github/workflows/docs.yml`, `.github/workflows/test.yml`, `.github/workflows/publish.yml`

### What was NOT inspected

- External GitHub Pages output on `gh-pages`
- Docker Hub and PyPI release state beyond the repo configuration
- Runtime behavior of the example stack or service mode
- Dynamic or cross-repo contracts outside this checkout
- Ad hoc local analysis artifacts such as `cover-report.md`, which were not treated as project source-of-truth files

### Heuristic limitations

This analysis is static. It can show where values are duplicated and where guards appear absent, but it cannot prove that a supposedly guarded path is fully covered. In particular, a `test-failure` propagation mode assumes the relevant branch of the test suite actually runs and asserts the broken case. Likewise, a `shared-import` classification assumes the downstream build step still executes in the environments that matter.
