"""Contract tests for the sh:ValidationReport serializer.

Implements the PALS's Law contract from the P3A plan: the serializer is
a generator of structured output, so it must be verifiable. We round-trip
the serializer's output through rdflib's own parser and assert that the
focus-node set reproduces the engine's recorded ``invalid_instances``.

Six tests:

1. ``test_serializer_produces_parsable_turtle`` — output parses cleanly.
2. ``test_serializer_produces_parsable_jsonld`` — same for JSON-LD.
3. ``test_roundtrip_invalid_instances_match_engine`` — PALS's Law contract.
4. ``test_source_component_emitted_per_constraint`` — every ValidationResult
   carries a sh:sourceConstraintComponent matching the constraint's
   SOURCE_COMPONENT.
5. ``test_severity_falls_back_correctly`` — constraint → shape → Violation
   fallback chain holds.
6. ``test_unsupported_format_raises_value_error`` — Q-02 distinction.
"""

from __future__ import annotations

import pytest
from rdflib import Graph, Namespace, RDF

from TravSHACL import parse_heuristics
from TravSHACL.core.GraphTraversal import GraphTraversal
from TravSHACL.core.ShapeSchema import ShapeSchema


SH = Namespace("http://www.w3.org/ns/shacl#")


def _build_schema(schema_dir: str) -> ShapeSchema:
    data_graph = Graph().parse("./tests/data/test.ttl")
    return ShapeSchema(
        schema_dir=schema_dir,
        schema_format="SHACL",
        endpoint=data_graph,
        graph_traversal=GraphTraversal.BFS,
        heuristics=parse_heuristics("TARGET IN BIG"),
        use_selective_queries=False,
        max_split_size=256,
        output_dir=None,
        order_by_in_queries=False,
        save_outputs=False,
    )


def _strip_angle_brackets(value: str) -> str:
    return value[1:-1] if value.startswith("<") and value.endswith(">") else value


def test_serializer_produces_parsable_turtle():
    """The serializer's Turtle output parses cleanly via rdflib."""
    schema = _build_schema("./tests/cases/single_shape/case1/shapes/")
    result_dict, turtle_str = schema.validate(report_format="turtle")
    assert isinstance(turtle_str, str)
    parsed = Graph().parse(data=turtle_str, format="turtle")
    assert (None, RDF.type, SH.ValidationReport) in parsed
    # sh:conforms must be present; checking via list() to avoid Literal(false) being falsy.
    assert list(parsed.objects(None, SH.conforms)), "sh:conforms not emitted"


def test_serializer_produces_parsable_jsonld():
    """The serializer's JSON-LD output parses cleanly via rdflib."""
    schema = _build_schema("./tests/cases/single_shape/case1/shapes/")
    result_dict, jsonld_str = schema.validate(report_format="jsonld")
    assert isinstance(jsonld_str, str)
    parsed = Graph().parse(data=jsonld_str, format="json-ld")
    assert (None, RDF.type, SH.ValidationReport) in parsed


def test_roundtrip_invalid_instances_match_engine():
    """PALS's Law: focus-node set in the serialized report matches engine's invalid_instances."""
    schema = _build_schema("./tests/cases/single_shape/case1/shapes/")
    result_dict, turtle_str = schema.validate(report_format="turtle")

    engine_invalid_per_shape = {}
    for shape_id, sets in result_dict.items():
        if shape_id == "unbound":
            continue
        engine_invalid_per_shape[_strip_angle_brackets(shape_id)] = {
            _strip_angle_brackets(target[1]) for target in sets.get("invalid_instances", set())
        }

    parsed = Graph().parse(data=turtle_str, format="turtle")
    report_invalid_per_shape = {}
    for result in parsed.subjects(RDF.type, SH.ValidationResult):
        source_shape = parsed.value(result, SH.sourceShape)
        focus_node = parsed.value(result, SH.focusNode)
        if source_shape is None or focus_node is None:
            continue
        key = _strip_angle_brackets(str(source_shape))
        report_invalid_per_shape.setdefault(key, set()).add(_strip_angle_brackets(str(focus_node)))

    for shape_id, focus_nodes in report_invalid_per_shape.items():
        engine_focus_nodes = engine_invalid_per_shape.get(shape_id, set())
        assert focus_nodes == engine_focus_nodes, (
            f"Report/engine focus-node mismatch for shape {shape_id}:\n"
            f"  report:  {sorted(focus_nodes)}\n"
            f"  engine:  {sorted(engine_focus_nodes)}"
        )

    for shape_id, engine_focus_nodes in engine_invalid_per_shape.items():
        if engine_focus_nodes:
            assert shape_id in report_invalid_per_shape, (
                f"Engine reported violations for {shape_id} but report has none"
            )


def test_source_component_emitted_per_constraint():
    """Every sh:ValidationResult carries a non-None sh:sourceConstraintComponent."""
    schema = _build_schema("./tests/cases/value_range/case1/shapes/")
    _, turtle_str = schema.validate(report_format="turtle")

    parsed = Graph().parse(data=turtle_str, format="turtle")
    results = list(parsed.subjects(RDF.type, SH.ValidationResult))
    assert results, "fixture should produce at least one ValidationResult"
    for result in results:
        component = parsed.value(result, SH.sourceConstraintComponent)
        assert component is not None, f"ValidationResult {result} missing sh:sourceConstraintComponent"
        assert str(component).startswith("http://www.w3.org/ns/shacl#"), (
            f"sourceConstraintComponent {component} is not a SHACL namespace IRI"
        )


def test_severity_falls_back_correctly():
    """Without explicit severity, all results emit sh:Violation default."""
    schema = _build_schema("./tests/cases/single_shape/case1/shapes/")
    _, turtle_str = schema.validate(report_format="turtle")
    parsed = Graph().parse(data=turtle_str, format="turtle")
    severities = set(parsed.objects(None, SH.resultSeverity))
    assert severities, "expected at least one sh:resultSeverity emission"
    for sev in severities:
        assert sev == SH.Violation, f"expected sh:Violation default, got {sev}"


def test_unsupported_format_raises_value_error():
    """Q-02 semantic distinction: unsupported format raises ValueError."""
    schema = _build_schema("./tests/cases/single_shape/case1/shapes/")
    with pytest.raises(ValueError, match="Unsupported"):
        schema.validate(report_format="xml")
