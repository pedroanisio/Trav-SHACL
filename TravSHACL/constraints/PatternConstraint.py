__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableType


class PatternConstraint(Constraint):
    """Represents sh:pattern constraints with optional sh:flags."""

    SOURCE_COMPONENT = "http://www.w3.org/ns/shacl#PatternConstraintComponent"

    def __init__(self, var_generator, id_, path, pattern, is_pos, options, flags=None, target_def=None):
        super().__init__(id_, is_pos, None, None, pattern, None, target_def, path, options)
        self.varGenerator = var_generator
        self.flags = flags
        self.max = 0
        self.variables = self.generate_variables(var_generator, VariableType.VALIDATION, 1)

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        value_var = self.variables[0]
        builder.add_triple(self.path_sparql(), "?" + value_var)
        args = ["STR(?" + value_var + ")", self.get_value()]
        if self.flags:
            args.append(self.flags)
        condition = "REGEX(" + ", ".join(args) + ")"
        builder.filters.append("!(" + condition + ")" if self.get_is_pos() else condition)
