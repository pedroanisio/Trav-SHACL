__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableType


class InConstraint(Constraint):
    """Represents sh:in enumeration constraints."""

    SOURCE_COMPONENT = "http://www.w3.org/ns/shacl#InConstraintComponent"

    def __init__(self, var_generator, id_, path, values, is_pos, options, target_def=None):
        super().__init__(id_, is_pos, None, None, tuple(values), None, target_def, path, options)
        self.varGenerator = var_generator
        self.min = -1
        self.max = 0
        self.variables = self.generate_variables(var_generator, VariableType.VALIDATION, 1)

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        value_var = self.variables[0]
        builder.add_triple(self.path_sparql(), "?" + value_var)
        allowed = ", ".join(self.get_value())
        condition = "?" + value_var + " IN (" + allowed + ")"
        builder.filters.append("!(" + condition + ")" if self.get_is_pos() else condition)
