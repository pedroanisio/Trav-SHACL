import pytest

from TravSHACL.core.Path import Inverse, PathExpression, Predicate, Sequence


def test_predicate_preserves_prefixed_name():
    path = PathExpression.from_string('test:property0')

    assert isinstance(path, Predicate)
    assert path.to_sparql() == 'test:property0'


def test_inverse_preserves_legacy_sparql_text():
    path = PathExpression.from_string('^<http://test.example.com/toA>')

    assert isinstance(path, Inverse)
    assert path.to_sparql() == '^<http://test.example.com/toA>'


def test_sequence_preserves_iri_segments():
    path = PathExpression.from_string('<http://test.example.com/toA>/<http://test.example.com/property0>')

    assert isinstance(path, Sequence)
    assert path.to_sparql() == '<http://test.example.com/toA>/<http://test.example.com/property0>'


def test_unwrapped_absolute_iri_becomes_predicate():
    path = PathExpression.from_string('http://test.example.com/toA')

    assert isinstance(path, Predicate)
    assert path.to_sparql() == '<http://test.example.com/toA>'


def test_sequence_rejects_empty_segment():
    with pytest.raises(ValueError, match='empty segment'):
        PathExpression.from_string('test:toA/')
