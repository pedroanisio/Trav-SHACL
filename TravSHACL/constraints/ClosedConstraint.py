__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableType

RDF_TYPE = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"


class ClosedConstraint(Constraint):
    """Represents sh:closed with parser-supplied allowed paths."""

    SOURCE_COMPONENT = "http://www.w3.org/ns/shacl#ClosedConstraintComponent"

    def __init__(self, var_generator, id_, allowed_paths, ignored_properties, is_pos, options, target_def=None):
        super().__init__(id_, is_pos, None, None, None, None, target_def, None, options)
        self.varGenerator = var_generator
        self.allowedPaths = tuple(allowed_paths)
        self.ignoredProperties = tuple(ignored_properties)
        self.min = -1
        self.max = 0
        self.variables = self.generate_variables(var_generator, VariableType.VALIDATION, 2)

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        predicate_var, object_var = self.variables
        builder.triples.append("?" + focus_var + " ?" + predicate_var + " ?" + object_var + ".")
        allowed = list(self.allowedPaths) + list(self.ignoredProperties) + [RDF_TYPE]
        if allowed:
            builder.filters.append("?" + predicate_var + " NOT IN (" + ", ".join(allowed) + ")")
