__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableType


class NotConstraint(Constraint):
    """Represents atomic property-shape sh:not constraints."""

    def __init__(self, var_generator, id_, nested_constraints, is_pos, options, target_def=None):
        super().__init__(id_, is_pos, None, None, None, None, target_def, None, options)
        self.varGenerator = var_generator
        self.nestedConstraints = tuple(nested_constraints)
        self.min = -1
        self.max = 0
        self.variables = self.generate_variables(var_generator, VariableType.VALIDATION, 1)

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        nested_builder = builder.sub_builder()
        for constraint in self.nestedConstraints:
            constraint.emit_filter(nested_builder, focus_var)
        pattern = nested_builder.get_triple_patterns()
        builder.filters.append("EXISTS { " + pattern + " }")
