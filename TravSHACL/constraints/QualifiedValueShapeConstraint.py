__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableType


class QualifiedValueShapeConstraint(Constraint):
    """Represents sh:qualifiedValueShape with min/max qualified counts."""

    SOURCE_COMPONENT = "http://www.w3.org/ns/shacl#QualifiedMinCountConstraintComponent"

    def __init__(
        self,
        var_generator,
        id_,
        path,
        shape_ref,
        qualified_min,
        qualified_max,
        is_pos,
        options,
        target_def=None,
    ):
        super().__init__(id_, is_pos, None, None, None, shape_ref, target_def, path, options)
        self.varGenerator = var_generator
        self.qualifiedMin = qualified_min
        self.qualifiedMax = qualified_max
        self.min = -1 if qualified_min is None else int(qualified_min)
        self.max = -1 if qualified_max is None else int(qualified_max)
        variable_count = self.min if self.min != -1 else self.max + 1
        self.variables = self.generate_variables(var_generator, VariableType.VALIDATION, variable_count)

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        variables = self.get_variables()
        if self.min != -1:
            for variable in variables:
                builder.inter_shape_refs[variable] = self.get_shape_ref()
                builder.triples.append("\n$inter_shape_type_to_add$")
                builder.add_triple(self.path_sparql(), "?" + variable)
            if len(variables) > 1:
                builder.add_cardinality_filter(variables)
            return

        for variable in variables:
            builder.inter_shape_refs[variable] = self.get_shape_ref()
            builder.triples.append("\n$inter_shape_type_to_add$")
            builder.add_triple(self.path_sparql(), "?" + variable)
        if len(variables) > 1:
            builder.add_cardinality_filter(variables)

    def compute_rule_pattern_body(self):
        return [(self.shapeRef, variable, self.isPos) for variable in self.variables] if self.shapeRef is not None else []

    def get_source_component(self):
        """Return QualifiedMinCount or QualifiedMaxCount component IRI based on which bound is set.

        Per ADR-006 Plan Reconciliation, the parser creates separate
        QualifiedValueShapeConstraint instances for qualifiedMin and
        qualifiedMax (one bound set per instance). This method picks the
        spec component IRI matching the bound the instance carries.
        """
        if self.qualifiedMax is not None and self.qualifiedMin is None:
            return "http://www.w3.org/ns/shacl#QualifiedMaxCountConstraintComponent"
        return "http://www.w3.org/ns/shacl#QualifiedMinCountConstraintComponent"
