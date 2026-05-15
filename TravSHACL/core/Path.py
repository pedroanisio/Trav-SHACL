from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlparse


class PathExpression:
    """Base class for parsed SHACL path expressions."""

    def to_sparql(self) -> str:
        raise NotImplementedError

    @staticmethod
    def from_string(path) -> PathExpression:
        if isinstance(path, PathExpression):
            return path
        if path is None:
            raise ValueError("Path expression cannot be None")

        path_string = str(path).strip()
        if not path_string:
            raise ValueError("Path expression cannot be empty")
        if not (path_string.startswith("<") and path_string.endswith(">")) and urlparse(path_string).netloc != "":
            path_string = "<" + path_string + ">"

        if path_string.startswith("^"):
            return Inverse(PathExpression.from_string(path_string[1:]))

        parts = _split_sequence(path_string)
        if len(parts) > 1:
            return Sequence(tuple(PathExpression.from_string(part) for part in parts))

        return Predicate(path_string)


@dataclass(frozen=True)
class Predicate(PathExpression):
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Predicate path cannot be empty")

    def to_sparql(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.to_sparql()


@dataclass(frozen=True)
class Inverse(PathExpression):
    path: PathExpression

    def to_sparql(self) -> str:
        return "^" + self.path.to_sparql()

    def __str__(self) -> str:
        return self.to_sparql()


@dataclass(frozen=True)
class Sequence(PathExpression):
    paths: tuple[PathExpression, ...]

    def __init__(self, paths: Iterable[PathExpression]):
        object.__setattr__(self, "paths", tuple(paths))
        if not self.paths:
            raise ValueError("Sequence path cannot be empty")

    def to_sparql(self) -> str:
        return "/".join(path.to_sparql() for path in self.paths)

    def __str__(self) -> str:
        return self.to_sparql()


def _split_sequence(path: str) -> list[str]:
    parts = []
    start = 0
    in_iri = False
    for i, char in enumerate(path):
        if char == "<":
            in_iri = True
        elif char == ">":
            in_iri = False
        elif char == "/" and not in_iri:
            part = path[start:i].strip()
            if not part:
                raise ValueError("Sequence path contains an empty segment")
            parts.append(part)
            start = i + 1

    if parts:
        final = path[start:].strip()
        if not final:
            raise ValueError("Sequence path contains an empty segment")
        parts.append(final)
    return parts or [path]
