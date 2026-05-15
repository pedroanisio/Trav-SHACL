__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableType


class PairEqualsConstraint(Constraint):
    """Represents sh:equals constraints."""

    def __init__(self, var_generator, id_, path, referenced_property, is_pos, options, target_def=None):
        super().__init__(
            id_, is_pos, None, None, referenced_property, None, target_def, path, options, referenced_property
        )
        self.varGenerator = var_generator
        self.max = 0
        self.variables = self.generate_variables(var_generator, VariableType.VALIDATION, 1)

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        value_var = self.variables[0]
        path = self.path_sparql()
        ref_path = self.referenced_property_sparql()
        builder.triples.append(
            "{ ?"
            + focus_var
            + " "
            + path
            + " ?"
            + value_var
            + " . FILTER NOT EXISTS { ?"
            + focus_var
            + " "
            + ref_path
            + " ?"
            + value_var
            + " . } } UNION { ?"
            + focus_var
            + " "
            + ref_path
            + " ?"
            + value_var
            + " . FILTER NOT EXISTS { ?"
            + focus_var
            + " "
            + path
            + " ?"
            + value_var
            + " . } }"
        )
