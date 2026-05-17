__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableType

RDF_TYPE = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
RDFS_SUBCLASS_OF = "<http://www.w3.org/2000/01/rdf-schema#subClassOf>"


class ClassConstraint(Constraint):
    """Represents sh:class constraints."""

    SOURCE_COMPONENT = "http://www.w3.org/ns/shacl#ClassConstraintComponent"

    def __init__(self, var_generator, id_, path, class_, is_pos, options, target_def=None):
        super().__init__(id_, is_pos, None, None, class_, None, target_def, path, options)
        self.varGenerator = var_generator
        self.max = 0
        self.variables = self.generate_variables(var_generator, VariableType.VALIDATION, 1)

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        value_var = self.variables[0]
        class_var = value_var + "_class"
        builder.add_triple(self.path_sparql(), "?" + value_var)
        class_pattern = (
            "{ ?"
            + value_var
            + " "
            + RDF_TYPE
            + " "
            + self.get_value()
            + " . } UNION { ?"
            + value_var
            + " "
            + RDF_TYPE
            + " ?"
            + class_var
            + " . ?"
            + class_var
            + " "
            + RDFS_SUBCLASS_OF
            + "+ "
            + self.get_value()
            + " . }"
        )
        condition = "EXISTS { " + class_pattern + " }"
        builder.filters.append("!(" + condition + ")" if self.get_is_pos() else condition)
