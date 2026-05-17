"""SHACL Validation Report serializer.

Builds a ``sh:ValidationReport`` graph from Trav-SHACL's per-shape
validation state and serializes it to Turtle or JSON-LD via rdflib.

Emits the SHACL §3 / §6.4 prescribed fields:

* ``sh:conforms`` (boolean) — True iff no shape has invalid targets.
* For each invalid target, one ``sh:ValidationResult`` carrying:
    - ``sh:focusNode`` — the failing instance IRI.
    - ``sh:sourceShape`` — the shape that flagged the focus.
    - ``sh:sourceConstraintComponent`` — the SHACL §4 component IRI,
      resolved via ``constraint.get_source_component()`` for the
      constraint(s) attached to the source shape.
    - ``sh:resultSeverity`` — falls back constraint.severity →
      shape.severity → ``sh:Violation`` default.
    - ``sh:resultMessage`` — constraint.description → shape.description
      → omitted.
    - ``sh:resultPath`` — included when the source shape's constraint
      that violated has a ``path_sparql()``.
    - ``sh:value`` — currently omitted; Trav-SHACL's engine does not
      surface per-value violations distinct from per-focus violations.
      Reserved for Phase 4+ extension.

PALS's Law: this is generated structured output. The companion test in
``tests/test_validation_report.py`` round-trips the serializer output
through rdflib's own parser and asserts the focus-node set matches the
engine's recorded ``invalid_instances``.
"""

from __future__ import annotations

from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import XSD

SH = Namespace("http://www.w3.org/ns/shacl#")

_SUPPORTED_FORMATS = {"turtle", "ttl", "jsonld", "json-ld"}


def serialize_validation_report(shapes_state, shapes_dict, fmt: str = "turtle") -> str:
    """Serialize the validation state as a ``sh:ValidationReport`` graph string.

    :param shapes_state: dict[shape_id, {"registered_targets": {"valid": set, "violated": set}, ...}]
        per ``ValidationState.shapes_state`` in TravSHACL/rule_based_validation/Validation.py.
    :param shapes_dict: dict[shape_id, Shape] — used to resolve shape-level
        severity, description, and to look up constraints for component IRIs.
    :param fmt: ``"turtle"`` (default) or ``"jsonld"``. Other formats raise ValueError
        per the Q-02 semantic distinction.
    :return: Serialized graph as a string.
    :raises ValueError: if ``fmt`` is not one of the supported formats.
    """
    if fmt not in _SUPPORTED_FORMATS:
        raise ValueError(
            "Unsupported validation report format: %r. Supported: %s" % (fmt, sorted(_SUPPORTED_FORMATS))
        )

    graph = Graph()
    graph.bind("sh", SH)

    report = BNode()
    graph.add((report, RDF.type, SH.ValidationReport))

    any_invalid = False
    for shape_id, shape_state in shapes_state.items():
        violated = shape_state.get("registered_targets", {}).get("violated", set())
        if not violated:
            continue
        any_invalid = True
        shape = shapes_dict.get(shape_id)
        for target in violated:
            graph.add((report, SH.result, _build_result(graph, target, shape)))

    graph.add((report, SH.conforms, Literal(not any_invalid, datatype=XSD.boolean)))

    rdflib_format = "turtle" if fmt in {"turtle", "ttl"} else "json-ld"
    return graph.serialize(format=rdflib_format)


def _build_result(graph: Graph, target, shape) -> BNode:
    """Construct one ``sh:ValidationResult`` blank node for a violated target."""
    result = BNode()
    graph.add((result, RDF.type, SH.ValidationResult))

    shape_id, instance_iri, _sign = target

    graph.add((result, SH.focusNode, _to_iri_or_literal(instance_iri)))
    graph.add((result, SH.sourceShape, _to_iri_or_literal(shape_id)))

    component = _resolve_component_iri(shape)
    if component is not None:
        graph.add((result, SH.sourceConstraintComponent, URIRef(component)))

    severity = _resolve_severity(shape)
    graph.add((result, SH.resultSeverity, severity))

    message = _resolve_message(shape)
    if message is not None:
        graph.add((result, SH.resultMessage, Literal(message)))

    path_sparql = _resolve_path(shape)
    if path_sparql is not None:
        graph.add((result, SH.resultPath, _to_iri_or_literal(path_sparql)))

    return result


def _to_iri_or_literal(value):
    """Strip angle-bracket wrapping if present and return a URIRef or Literal."""
    if value is None:
        return Literal("")
    s = str(value)
    if s.startswith("<") and s.endswith(">"):
        s = s[1:-1]
    if "://" in s or s.startswith("urn:"):
        return URIRef(s)
    return Literal(s)


def _resolve_component_iri(shape):
    """Return the first non-None component IRI from the shape's constraints."""
    if shape is None:
        return None
    for constraint in getattr(shape, "constraints", []) or []:
        component = constraint.get_source_component()
        if component:
            return component
    return None


def _resolve_severity(shape):
    """Resolve sh:resultSeverity per the constraint → shape → Violation fallback."""
    if shape is not None:
        for constraint in getattr(shape, "constraints", []) or []:
            severity = constraint.get_severity()
            if severity:
                return _severity_to_uri(severity)
        shape_severity = getattr(shape, "get_severity", lambda: None)()
        if shape_severity:
            return _severity_to_uri(shape_severity)
    return SH.Violation


def _severity_to_uri(severity):
    s = str(severity)
    if s.startswith("<") and s.endswith(">"):
        s = s[1:-1]
    if "://" in s:
        return URIRef(s)
    return URIRef("http://www.w3.org/ns/shacl#" + s)


def _resolve_message(shape):
    """sh:resultMessage from constraint.description → shape.description, else None."""
    if shape is None:
        return None
    for constraint in getattr(shape, "constraints", []) or []:
        desc = constraint.get_description()
        if desc:
            return desc
    return getattr(shape, "description", None) or None


def _resolve_path(shape):
    """sh:resultPath SPARQL form from the first constraint that has one."""
    if shape is None:
        return None
    for constraint in getattr(shape, "constraints", []) or []:
        path_sparql = constraint.path_sparql()
        if path_sparql:
            return path_sparql
    return None
