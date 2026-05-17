# v1.10.0 - 17 May 2026
- **Full SHACL Core compliance milestone** — closes the Phase 1-3 compliance effort (8 commits from `4286b7d` through this release). See `cover-report-phase-3.md` for the final gap-closure status.
- 27 polymorphic `Constraint` subclasses now declare a `SOURCE_COMPONENT` class attribute mapping to the SHACL §4 component IRI; enforced by a new drift guard.
- New `TravSHACL.output.serialize_validation_report` emits a spec-conformant `sh:ValidationReport` graph (Turtle or JSON-LD) via `ShapeSchema.validate(report_format='turtle' | 'jsonld')`. The previous default `validate()` signature returns the per-shape dict byte-identically (side-by-side API).
- PALS's Law contract: `tests/test_validation_report.py::test_roundtrip_invalid_instances_match_engine` rounds the serializer output back through rdflib and asserts the focus-node set matches the engine's classification.
- `AndConstraint` and `XoneConstraint` engine saturation bug fixed via a polymorphic `participates_in_min_query()` accessor and target-passthrough triple emission. New end-to-end fixtures: `tests/cases/logical_constraints/case3` (sh:and), `case4` (sh:xone, with K-02 caveat). See ADR-009.
- JSON shape format **formally deprecated**; will be removed in v2.0.0. The `DeprecationWarning` now cites the explicit removal version and points to `docs/adr/ADR-010-json-format-deprecation.md` for the policy.
- 10 ADRs total (ADR-001 through ADR-010) now document the architectural decisions across the compliance effort.

# v1.9.0 - 06 May 2025
- Fix check for parsing shapes with `sh:or` constraints
- Add switch `ignore_parsing_errors` to `ShapeSchema` to either log a warning or throw an exception for parsing errors

# v1.8.3 - 05 May 2025
- Log a warning message instead of throwing `NotImplementedError`
- Extend shape parser to recognize sequence paths

# v1.8.2 - 02 May 2025
- Skip unsupported constraints; logs a warning instead of throwing an exception

# v1.8.1 - 30 Apr 2025
- Fix parsing issue for shapes with `sh:property` and `sh:sparql`

# v1.8.0 - 24 Feb 2025
- Add support for Python 3.13
- Drop support for Python 3.8
- Update dependencies
- Update documentation
- Update the Python version for the Docker image (3.12.5 to 3.12.9)
- Update the Virtuoso version in tests and example to 7.2.14

# v1.7.2 - 09 Sep 2024
- Mark the JSON format for shape schemas as deprecated
- Update dependencies
- Minor updates of documentation
- Update the Python version for the Docker image (3.11.5 to 3.12.5)
- Update the Virtuoso version in tests and example to 7.2.13

# v1.7.1 - 06 Apr 2024
- Raise `NotImplementedError` stating that an unsupported feature was used instead of `UnboundLocalError: cannot access local variable 'dict_1'`

# v1.7.0 - 23 Nov 2023
- Add feature to pass an `rdflib.Graph` instead of a schema directory

# v1.6.0 - 14 Nov 2023
- Add feature to validate private SPARQL endpoints via HTTP Basic Auth
- Add Python 3.12 support
- Minor maintenance updates

# v1.5.1 - 17 Oct 2023
- Fix necessity of adding a slash (/) at the end of the output path
- Update trace keeping
- Minor updates of documentation

# v1.5.0 - 21 Sep 2023
- Fix parameter `endpoint` for Flask app
- Reduce the number of entities in the example
- Update the Python version for the Docker image (3.9.13 to 3.11.5)
- Update the Virtuoso version in tests and example to 7.2.10
- Update GitHub Action for the test suite to run in parallel
- Update init method of `ShapeSchema`
  - All parameters are now keyword-only and typed
  - Only `shape_dir` and `endpoint` are required
  - Add default values for the remaining parameters
- Code clean up and structural improvements
- Add documentation to GitHub pages

# v1.4.2 - 19 Jul 2023
- The raw representation of OR constraints is no longer kept after parsing the constraint
- Fix issue with OR query when there are no constraints

# v1.4.1 - 18 Jul 2023
- Refactor parsing of OR constraints

# v1.4.0 - 13 Jul 2023
- Add capability of executing simple OR constraints, i.e., minimal or maximal occurrence of a predicate
- Add capability to handle inverse paths ``sh:path [ sh:inversePath ex:your_predicate ]``
- Add test cases for the above-mentioned features
- Update dependencies
- Drop Python 3.7 support
- Add Python 3.11 support

# v1.3.2 - 09 Jul 2023
- Add option for creating only one single connected component to ``TravSHACL.core.GraphTraversal.traverse_graph()``

# v1.3.1 - 27 Jun 2023
- Remove print of execution time

# v1.3.0 - 17 Feb 2023
- Add feature for basic SPARQL constraints
- Add feature to validate RDFLib graphs
- Improve finding of shape files
- Easier import of important parts of Trav-SHACL
- Add more test cases

# v1.2.0 - 01 Feb 2023
- Add feature of target query in RDF input

# v1.1.2 - 30 Jan 2023
- Fix referencing shapes when using TTL input
- Print report to console only if it is not stored in file

# v1.1.1 - 15 Dec 2022
- Fix not changing endpoint URL when using the interface

# v1.1.0 - 14 Dec 2022
- Temporary fix for `MinMaxConstraints`
- Add simple validation interface
- Add parsing of more than one shape per file (in Turtle format only)
- Fix issue with multiple connected components in the SHACL schema
- Fix for referencing shapes when using Turtle format

# v1.0.2 - 03 Aug 2022
- Fix inferred state of targets of shape without constraints
- Include the type statement for the referencing shape in max inter-shape constraint queries

# v1.0.1 - 02 Aug 2022
- Fix max constraint query for cases where the target query contains several triple patterns

# v1.0.0 - 13 Jul 2022
- First release of Trav-SHACL