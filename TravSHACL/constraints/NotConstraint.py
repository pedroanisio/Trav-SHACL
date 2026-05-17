__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableType


class NotConstraint(Constraint):
    """Represents atomic property-shape sh:not constraints.

    DEC-05 carry-over: only atomic property-shape negation is supported.
    Shape-reference sh:not (e.g., sh:not [sh:node :OtherShape]) raises
    NotImplementedError at parse time.

    Engine semantics: ``max = 0`` combined with the nested triple pattern
    means a focus is INVALID when the nested pattern matches it (i.e.,
    the focus satisfies the inner constraint, which the outer sh:not
    rejects). The engine's cardinality-counting logic in interleave
    treats max=0 as "any match invalidates", which is exactly the
    semantics we want.

    Implementation: emit the nested constraint's emit_filter directly
    into the parent QueryBuilder. The outer max-query then enumerates
    focus nodes where the nested pattern matches; with max=0, those
    focus nodes are classified invalid. No FILTER NOT EXISTS wrapper
    is needed — the polarity comes from max=0 alone.
    """

    SOURCE_COMPONENT = "http://www.w3.org/ns/shacl#NotConstraintComponent"

    def __init__(self, var_generator, id_, nested_constraints, is_pos, options, target_def=None):
        super().__init__(id_, is_pos, None, None, None, None, target_def, None, options)
        self.varGenerator = var_generator
        self.nestedConstraints = tuple(nested_constraints)
        self.min = -1
        self.max = 0
        self.variables = self.generate_variables(var_generator, VariableType.VALIDATION, 1)
        # Re-expose the nested constraint's path so the engine's path-aware
        # cardinality logic can drive max=0 invalidation correctly.
        for constraint in self.nestedConstraints:
            if constraint.path is not None:
                self.path = constraint.path
                break

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        """Emit the nested pattern directly so ?focus_var gets bound; max=0 handles negation."""
        for constraint in self.nestedConstraints:
            constraint.emit_filter(builder, focus_var)
