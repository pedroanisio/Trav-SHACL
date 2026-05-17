__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableType


class PairLessThanOrEqualsConstraint(Constraint):
    """Represents sh:lessThanOrEquals constraints."""

    SOURCE_COMPONENT = "http://www.w3.org/ns/shacl#LessThanOrEqualsConstraintComponent"

    def __init__(self, var_generator, id_, path, referenced_property, is_pos, options, target_def=None):
        super().__init__(
            id_, is_pos, None, None, referenced_property, None, target_def, path, options, referenced_property
        )
        self.varGenerator = var_generator
        self.max = 0
        self.variables = self.generate_variables(var_generator, VariableType.VALIDATION, 2)

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        left, right = self.variables
        builder.add_triple(self.path_sparql(), "?" + left)
        builder.add_triple(self.referenced_property_sparql(), "?" + right)
        condition = "?" + left + " <= ?" + right
        builder.filters.append("!(" + condition + ")" if self.get_is_pos() else condition)
