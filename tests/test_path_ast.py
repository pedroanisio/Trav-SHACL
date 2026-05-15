import pytest
from TravSHACL.core.Path import (
    Alternative,
    Inverse,
    OneOrMore,
    PathExpression,
    Predicate,
    Sequence,
    ZeroOrMore,
    ZeroOrOne,
)


def test_predicate_preserves_prefixed_name():
    path = PathExpression.from_string("test:property0")

    assert isinstance(path, Predicate)
    assert path.to_sparql() == "test:property0"


def test_inverse_preserves_legacy_sparql_text():
    path = PathExpression.from_string("^<http://test.example.com/toA>")

    assert isinstance(path, Inverse)
    assert path.to_sparql() == "^<http://test.example.com/toA>"


def test_sequence_preserves_iri_segments():
    path = PathExpression.from_string("<http://test.example.com/toA>/<http://test.example.com/property0>")

    assert isinstance(path, Sequence)
    assert path.to_sparql() == "<http://test.example.com/toA>/<http://test.example.com/property0>"


def test_unwrapped_absolute_iri_becomes_predicate():
    path = PathExpression.from_string("http://test.example.com/toA")

    assert isinstance(path, Predicate)
    assert path.to_sparql() == "<http://test.example.com/toA>"


def test_sequence_rejects_empty_segment():
    with pytest.raises(ValueError, match="empty segment"):
        PathExpression.from_string("test:toA/")


def test_extended_path_nodes_emit_sparql_property_path_syntax():
    first = Predicate("<http://test.example.com/first>")
    second = Predicate("<http://test.example.com/second>")

    assert Alternative([first, second]).to_sparql() == "(<http://test.example.com/first>|<http://test.example.com/second>)"
    assert ZeroOrMore(first).to_sparql() == "<http://test.example.com/first>*"
    assert OneOrMore(first).to_sparql() == "<http://test.example.com/first>+"
    assert ZeroOrOne(first).to_sparql() == "<http://test.example.com/first>?"


def test_alternative_rejects_single_option():
    with pytest.raises(ValueError, match="at least two"):
        Alternative([Predicate("test:only")])
