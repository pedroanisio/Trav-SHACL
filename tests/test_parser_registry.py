import pytest
from rdflib import Graph
from TravSHACL.constraints.ClassConstraint import ClassConstraint
from TravSHACL.constraints.ClosedConstraint import ClosedConstraint
from TravSHACL.constraints.HasValueConstraint import HasValueConstraint
from TravSHACL.constraints.InConstraint import InConstraint
from TravSHACL.constraints.LanguageInConstraint import LanguageInConstraint
from TravSHACL.constraints.NodeKindConstraint import NodeKindConstraint
from TravSHACL.constraints.PairEqualsConstraint import PairEqualsConstraint
from TravSHACL.constraints.QualifiedValueShapeConstraint import QualifiedValueShapeConstraint
from TravSHACL.constraints.RangeMinInclusiveConstraint import RangeMinInclusiveConstraint
from TravSHACL.constraints.UniqueLangConstraint import UniqueLangConstraint
from TravSHACL.core.GraphTraversal import GraphTraversal
from TravSHACL.core.Path import Alternative, OneOrMore, Predicate, ZeroOrMore, ZeroOrOne
from TravSHACL.core.ShapeParser import CONSTRAINT_DISPATCH, NAMESPACE_SHACL, ShapeParser
from TravSHACL.core.ShapeSchema import ShapeSchema
from TravSHACL.sparql.SPARQLEndpoint import SPARQLEndpoint

EXPECTED_IRIS = {
    "path",
    "minCount",
    "maxCount",
    "qualifiedMinCount",
    "qualifiedMaxCount",
    "datatype",
    "qualifiedValueShape",
    "node",
    "value",
    "not",
    "class",
    "nodeKind",
    "minInclusive",
    "minExclusive",
    "maxInclusive",
    "maxExclusive",
    "minLength",
    "maxLength",
    "pattern",
    "languageIn",
    "uniqueLang",
    "equals",
    "disjoint",
    "lessThan",
    "lessThanOrEquals",
}


def _parse_ttl(source, ignore_errors=False):
    return ShapeParser(ignore_errors=ignore_errors).parse_ttl(
        Graph().parse(data=source, format="ttl"),
        use_selective_queries=True,
        max_split_size=256,
        order_by_in_queries=False,
    )


def test_registry_covers_existing_iris():
    expected = {NAMESPACE_SHACL + name for name in EXPECTED_IRIS}
    assert expected <= set(CONSTRAINT_DISPATCH)


def test_unknown_iri_raises():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:property [
            sh:path test:property0 ;
            test:unsupportedConstraint 1
          ] .
    """

    with pytest.raises(NotImplementedError, match="unsupportedConstraint"):
        _parse_ttl(source)


def test_unknown_iri_warns_when_ignore_errors(caplog):
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:property [
            sh:path test:property0 ;
            test:unsupportedConstraint 1
          ] .
    """

    shapes = _parse_ttl(source, ignore_errors=True)

    assert len(shapes) == 1
    assert shapes[0].get_constraints() == []
    assert "Unsupported SHACL constraint IRI" in caplog.text


def test_dispatch_uses_full_iris_not_substrings():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:property [
            sh:path test:property0 ;
            test:MyMinThing 1
          ] .
    """

    with pytest.raises(NotImplementedError, match="MyMinThing"):
        _parse_ttl(source)


def test_shape_and_constraint_metadata_are_captured():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:deactivated true ;
          sh:name "Class A shape" ;
          sh:description "Shape description" ;
          sh:severity sh:Warning ;
          sh:property [
            sh:path test:property0 ;
            sh:minCount 1 ;
            sh:severity sh:Info ;
            sh:name "property minimum" ;
            sh:description "Constraint description" ;
            sh:order 1 ;
            sh:defaultValue "fallback"
          ] .
    """

    shape = _parse_ttl(source)[0]
    constraint = shape.get_constraints()[0]

    assert shape.is_deactivated() is True
    assert shape.get_name() == "Class A shape"
    assert shape.get_description() == "Shape description"
    assert shape.get_severity() == NAMESPACE_SHACL + "Warning"
    assert constraint.get_name() == "property minimum"
    assert constraint.get_description() == "Constraint description"
    assert constraint.get_severity() == NAMESPACE_SHACL + "Info"
    assert constraint.get_order() == "1"
    assert constraint.get_default_value() == "fallback"


def test_property_shape_is_parsed_as_first_class_shape():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassAProperty a sh:PropertyShape ;
          sh:path test:property0 ;
          sh:minCount 1 .
    """

    shape = _parse_ttl(source)[0]

    assert shape.get_id() == "<http://test.example.com/shapes/ClassAProperty>"
    assert shape.get_shape_kind() == "PropertyShape"
    assert shape.get_target_query() is None
    assert isinstance(shape.get_constraints()[0].path, Predicate)
    assert shape.get_constraints()[0].path.to_sparql() == "<http://test.example.com/property0>"


def test_property_shape_target_is_parsed():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassAProperty a sh:PropertyShape ;
          sh:targetClass test:ClassA ;
          sh:path test:property0 ;
          sh:minCount 1 .
    """

    shape = _parse_ttl(source)[0]

    assert shape.get_shape_kind() == "PropertyShape"
    assert shape.get_target_type() == "class"
    assert shape.get_target_def() == "<http://test.example.com/ClassA>"


def test_target_subjects_of_is_parsed():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :SubjectsOfToA a sh:NodeShape ;
          sh:targetSubjectsOf test:toA ;
          sh:property [
            sh:path test:property0 ;
            sh:minCount 1
          ] .
    """

    shape = _parse_ttl(source)[0]

    assert shape.get_target_type() == "subjectsOf"
    assert shape.get_target_def() == "<http://test.example.com/toA>"
    assert shape.get_target_query() == "SELECT ?x WHERE { ?x <http://test.example.com/toA> ?target }"


def test_target_objects_of_is_parsed():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ObjectsOfToA a sh:NodeShape ;
          sh:targetObjectsOf test:toA ;
          sh:property [
            sh:path test:property0 ;
            sh:minCount 1
          ] .
    """

    shape = _parse_ttl(source)[0]

    assert shape.get_target_type() == "objectsOf"
    assert shape.get_target_def() == "<http://test.example.com/toA>"
    assert shape.get_target_query() == "SELECT ?x WHERE { ?target <http://test.example.com/toA> ?x }"


def test_implicit_rdfs_class_target_is_parsed():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix test: <http://test.example.com/> .

        test:ClassA a sh:NodeShape, rdfs:Class ;
          sh:property [
            sh:path test:property0 ;
            sh:minCount 1
          ] .
    """

    shape = _parse_ttl(source)[0]

    assert shape.get_target_type() == "implicitClass"
    assert shape.get_target_def() == "<http://test.example.com/ClassA>"
    assert shape.get_target_query() == "SELECT ?x WHERE { ?x a <http://test.example.com/ClassA> }"


def test_value_type_constraints_are_parsed():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:property [
            sh:path test:toA ;
            sh:class test:ClassA ;
            sh:nodeKind sh:IRI
          ] .
    """

    constraints = _parse_ttl(source)[0].get_constraints()

    assert [type(constraint) for constraint in constraints] == [ClassConstraint, NodeKindConstraint]
    assert constraints[0].get_shape_ref() is None
    assert constraints[0].get_value() == "<http://test.example.com/ClassA>"


def test_invalid_node_kind_value_raises_value_error():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:property [
            sh:path test:toA ;
            sh:nodeKind test:NotANodeKind
          ] .
    """

    with pytest.raises(ValueError, match="Unsupported sh:nodeKind"):
        _parse_ttl(source)


def test_typed_range_literal_is_preserved_for_sparql_comparison():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:property [
            sh:path test:property1 ;
            sh:minInclusive "1990"^^xsd:integer
          ] .
    """

    constraint = _parse_ttl(source)[0].get_constraints()[0]

    assert isinstance(constraint, RangeMinInclusiveConstraint)
    assert constraint.get_value() == '"1990"^^<http://www.w3.org/2001/XMLSchema#integer>'


def test_language_and_unique_lang_constraints_are_parsed():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:property [
            sh:path test:label ;
            sh:languageIn ( "en" "pt" ) ;
            sh:uniqueLang true
          ] .
    """

    constraints = _parse_ttl(source)[0].get_constraints()

    assert [type(constraint) for constraint in constraints] == [LanguageInConstraint, UniqueLangConstraint]
    assert constraints[0].get_value() == ['"en"', '"pt"']


def test_pair_constraint_uses_referenced_property_not_shape_ref():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:property [
            sh:path test:property1 ;
            sh:equals test:property2
          ] .
    """

    shape = _parse_ttl(source)[0]
    constraint = shape.get_constraints()[0]

    assert isinstance(constraint, PairEqualsConstraint)
    assert constraint.get_shape_ref() is None
    assert constraint.referenced_property_sparql() == "<http://test.example.com/property2>"
    assert shape.get_shape_refs() == []


def test_extended_shacl_paths_are_parsed_from_turtle_blank_nodes():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:property [
            sh:path [ sh:alternativePath ( test:p1 test:p2 ) ] ;
            sh:minCount 1
          ] ;
          sh:property [
            sh:path [ sh:zeroOrMorePath test:p3 ] ;
            sh:minCount 1
          ] ;
          sh:property [
            sh:path [ sh:oneOrMorePath test:p4 ] ;
            sh:minCount 1
          ] ;
          sh:property [
            sh:path [ sh:zeroOrOnePath test:p5 ] ;
            sh:minCount 1
          ] .
    """

    paths = [constraint.path for constraint in _parse_ttl(source)[0].get_constraints()]

    assert [type(path) for path in paths] == [Alternative, ZeroOrMore, OneOrMore, ZeroOrOne]
    assert paths[0].to_sparql() == "(<http://test.example.com/p1>|<http://test.example.com/p2>)"
    assert paths[1].to_sparql() == "<http://test.example.com/p3>*"
    assert paths[2].to_sparql() == "<http://test.example.com/p4>+"
    assert paths[3].to_sparql() == "<http://test.example.com/p5>?"


def test_qualified_value_shape_uses_dedicated_constraint_not_plain_cardinality():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:property [
            sh:path test:toB ;
            sh:qualifiedValueShape [ sh:node :ClassB ] ;
            sh:qualifiedMinCount 1 ;
            sh:qualifiedMaxCount 2
          ] .

        :ClassB a sh:NodeShape ;
          sh:targetClass test:ClassB .
    """

    constraints = _parse_ttl(source)[0].get_constraints()

    assert [type(constraint) for constraint in constraints] == [
        QualifiedValueShapeConstraint,
        QualifiedValueShapeConstraint,
    ]
    assert constraints[0].get_shape_ref() == "<http://test.example.com/shapes/ClassB>"
    assert constraints[0].min == 1
    assert constraints[0].max == -1
    assert constraints[1].min == -1
    assert constraints[1].max == 2


def test_closed_has_value_and_in_constraints_are_parsed():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:closed true ;
          sh:ignoredProperties ( test:ignored ) ;
          sh:property [
            sh:path test:status ;
            sh:hasValue "active" ;
            sh:in ( "active" "pending" )
          ] .
    """

    constraints = _parse_ttl(source)[0].get_constraints()

    assert [type(constraint) for constraint in constraints] == [ClosedConstraint, HasValueConstraint, InConstraint]
    assert constraints[0].allowedPaths == ("<http://test.example.com/status>",)
    assert constraints[0].ignoredProperties == ("<http://test.example.com/ignored>",)
    assert constraints[1].get_value() == '"active"'
    assert constraints[2].get_value() == ('"active"', '"pending"')


def test_closed_has_value_and_in_constraints_validate_graph(tmp_path):
    SPARQLEndpoint.instance = None
    schema_dir = tmp_path / "shapes"
    schema_dir.mkdir()
    (schema_dir / "Thing.ttl").write_text(
        """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :Thing a sh:NodeShape ;
          sh:targetClass test:Thing ;
          sh:closed true ;
          sh:ignoredProperties ( test:ignored ) ;
          sh:property [
            sh:path test:status ;
            sh:hasValue "active" ;
            sh:in ( "active" "pending" )
          ] .
        """,
        encoding="utf-8",
    )
    data = Graph().parse(
        data="""
        @prefix test: <http://test.example.com/> .

        test:GoodThing a test:Thing ;
          test:status "active" ;
          test:ignored "ok" .

        test:MissingRequiredStatus a test:Thing ;
          test:ignored "ok" .

        test:BadStatusThing a test:Thing ;
          test:status "archived" .

        test:ExtraPropertyThing a test:Thing ;
          test:status "active" ;
          test:extra "not allowed" .
        """,
        format="ttl",
    )

    result = ShapeSchema(
        schema_dir=str(schema_dir),
        schema_format="SHACL",
        endpoint=data,
        graph_traversal=GraphTraversal.BFS,
        heuristics=None,
        use_selective_queries=True,
        max_split_size=256,
        output_dir=None,
        order_by_in_queries=False,
        save_outputs=False,
    ).validate()

    valid = sorted(instance[1] for values in result.values() for instance in values.get("valid_instances", []))
    invalid = sorted(instance[1] for values in result.values() for instance in values.get("invalid_instances", []))

    assert valid == ["http://test.example.com/GoodThing"]
    assert invalid == [
        "http://test.example.com/BadStatusThing",
        "http://test.example.com/ExtraPropertyThing",
        "http://test.example.com/MissingRequiredStatus",
    ]
    SPARQLEndpoint.instance = None


def test_shape_reference_not_raises_not_implemented():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:not :ClassB .

        :ClassB a sh:NodeShape ;
          sh:targetClass test:ClassB .
    """

    with pytest.raises(NotImplementedError, match="Shape-reference sh:not"):
        _parse_ttl(source)


def test_xone_raises_not_implemented_instead_of_silent_and_semantics():
    source = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :ClassA a sh:NodeShape ;
          sh:targetClass test:ClassA ;
          sh:xone ( :ClassB :ClassC ) .

        :ClassB a sh:NodeShape ;
          sh:targetClass test:ClassB .

        :ClassC a sh:NodeShape ;
          sh:targetClass test:ClassC .
    """

    with pytest.raises(NotImplementedError, match="sh:xone"):
        _parse_ttl(source)


def test_language_in_and_unique_lang_validate_language_tagged_literals(tmp_path):
    schema_dir = tmp_path / "shapes"
    schema_dir.mkdir()
    (schema_dir / "Thing.ttl").write_text(
        """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix test: <http://test.example.com/> .
        @prefix : <http://test.example.com/shapes/> .

        :Thing a sh:NodeShape ;
          sh:targetClass test:Thing ;
          sh:property [
            sh:path test:label ;
            sh:languageIn ( "en" "pt" ) ;
            sh:uniqueLang true
          ] .
        """,
        encoding="utf-8",
    )
    data = Graph().parse(
        data="""
        @prefix test: <http://test.example.com/> .

        test:ValidThing a test:Thing ;
          test:label "hello"@en, "ola"@pt .

        test:BadLanguageThing a test:Thing ;
          test:label "hallo"@de .

        test:DuplicateLanguageThing a test:Thing ;
          test:label "hello"@en, "hi"@en .
        """,
        format="ttl",
    )

    result = ShapeSchema(
        schema_dir=str(schema_dir),
        schema_format="SHACL",
        endpoint=data,
        graph_traversal=GraphTraversal.BFS,
        heuristics=None,
        use_selective_queries=True,
        max_split_size=256,
        output_dir=None,
        order_by_in_queries=False,
        save_outputs=False,
    ).validate()

    valid = sorted(instance[1] for values in result.values() for instance in values.get("valid_instances", []))
    invalid = sorted(instance[1] for values in result.values() for instance in values.get("invalid_instances", []))

    assert valid == ["http://test.example.com/ValidThing"]
    assert invalid == [
        "http://test.example.com/BadLanguageThing",
        "http://test.example.com/DuplicateLanguageThing",
    ]
