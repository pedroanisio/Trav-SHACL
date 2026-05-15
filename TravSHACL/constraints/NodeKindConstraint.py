__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableType

SHACL = "http://www.w3.org/ns/shacl#"

NODE_KIND_FILTERS = {
    SHACL + "IRI": "isIRI(?{var})",
    SHACL + "BlankNode": "isBlank(?{var})",
    SHACL + "Literal": "isLiteral(?{var})",
    SHACL + "BlankNodeOrIRI": "(isBlank(?{var}) || isIRI(?{var}))",
    SHACL + "BlankNodeOrLiteral": "(isBlank(?{var}) || isLiteral(?{var}))",
    SHACL + "IRIOrLiteral": "(isIRI(?{var}) || isLiteral(?{var}))",
}


class NodeKindConstraint(Constraint):
    """Represents sh:nodeKind constraints."""

    def __init__(self, var_generator, id_, path, node_kind, is_pos, options, target_def=None):
        if node_kind.strip("<>") not in NODE_KIND_FILTERS:
            raise ValueError("Unsupported sh:nodeKind value: " + node_kind)
        super().__init__(id_, is_pos, None, None, node_kind, None, target_def, path, options)
        self.varGenerator = var_generator
        self.max = 0
        self.variables = self.generate_variables(var_generator, VariableType.VALIDATION, 1)

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        value_var = self.variables[0]
        builder.add_triple(self.path_sparql(), "?" + value_var)
        condition = NODE_KIND_FILTERS[self.get_value().strip("<>")].format(var=value_var)
        builder.filters.append("!(" + condition + ")" if self.get_is_pos() else condition)
