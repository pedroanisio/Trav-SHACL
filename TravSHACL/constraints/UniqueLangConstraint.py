__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableType


class UniqueLangConstraint(Constraint):
    """Represents sh:uniqueLang constraints."""

    def __init__(self, var_generator, id_, path, is_pos, options, target_def=None):
        super().__init__(id_, is_pos, None, None, "true", None, target_def, path, options)
        self.varGenerator = var_generator
        self.max = 0
        self.variables = self.generate_variables(var_generator, VariableType.VALIDATION, 2)

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        first, second = self.variables
        path = self.path_sparql()
        builder.add_triple(path, "?" + first)
        builder.add_triple(path, "?" + second)
        condition = (
            "?"
            + first
            + " != ?"
            + second
            + " && LANG(?"
            + first
            + ') != "" && LANG(?'
            + first
            + ") = LANG(?"
            + second
            + ")"
        )
        builder.filters.append(condition if self.get_is_pos() else "!(" + condition + ")")
