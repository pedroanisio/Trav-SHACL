__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.core.Path import PathExpression


class Constraint:
    """Base class for all constraints."""

    def __init__(
        self,
        id_=None,
        is_pos=None,
        satisfied=None,
        datatype=None,
        value=None,
        shape_ref=None,
        target_def=None,
        path=None,
        options=None,
        referenced_property=None,
    ):
        """
        Base constructor for all constraints.

        :param id_: name of the constraint
        :param is_pos: true if it is a positive constraint, false otherwise
        :param satisfied: indicates whether the constraint is satisfied, should be unknown at creation
        :param datatype: contains the datatype the object must fulfill
        :param value: contains the value the constraint checks again, i.e., an object
        :param shape_ref: contains the name of the shape referenced by the constraint, none otherwise
        :param target_def: contains the target definition of the shape the constraint belongs to if it has one
        :param path: the path associated with this constraint, e.g., a predicate
        :param options: gets the options to be used in or_operation
        :param referenced_property: a second SHACL property path used by pair constraints
        """
        self.id = id_
        self.isPos = is_pos
        self.satisfied = satisfied
        self.options = options
        self.datatype = datatype
        self.value = value
        self.shapeRef = shape_ref
        self.target = target_def
        self.min = -1
        self.max = -1

        self.variables = []
        self.path = None if path is None else PathExpression.from_string(path)
        self.referencedProperty = (
            None if referenced_property is None else PathExpression.from_string(referenced_property)
        )
        self.severity = None
        self.name = None
        self.description = None
        self.group = None
        self.order = None
        self.defaultValue = None

    def get_datatype(self):
        return self.datatype

    def get_value(self):
        return self.value

    def get_shape_ref(self):
        return self.shapeRef

    def get_severity(self):
        return self.severity

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_group(self):
        return self.group

    def get_order(self):
        return self.order

    def get_default_value(self):
        return self.defaultValue

    def get_id(self):
        return self.id

    def get_is_pos(self):
        return self.isPos

    def get_options(self):
        return self.options

    def path_sparql(self):
        return None if self.path is None else self.path.to_sparql()

    def referenced_property_sparql(self):
        return None if self.referencedProperty is None else self.referencedProperty.to_sparql()

    def is_sparql_constraint(self):
        return False

    def is_min_only_constraint(self):
        return False

    def is_max_only_constraint(self):
        return False

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        """
        Adds the necessary triples and filters for this constraint to a QueryBuilder.

        :param builder: query builder receiving triple patterns and filters
        :param focus_var: focus node variable name
        :param or_value: used in the case of multiple 'or' for triple grouping
        :param or_affix: used in the case of more than one or triple within an option in an 'or' operation
        :param maxonly: whether to emit the OR-specific max-cardinality representation
        """
        variables = self.get_variables()
        path = self.path_sparql()
        if path is None:
            return

        if maxonly:
            v = variables[0]
            builder.add_union_triples(path, "?" + v, or_value, or_affix, True, card=self.max)
            return

        if self.get_value() is not None:
            if or_value > 0:
                builder.add_union_triples(path, self.get_value(), or_value, or_affix)
            else:
                builder.add_triple(path, self.get_value())
            return

        if or_value > 0:
            v = variables[0]
            builder.add_union_triples(path, "?" + v, or_value, or_affix, card=self.min)
        else:
            for v in variables:
                if self.get_shape_ref() is not None:
                    builder.inter_shape_refs[v] = self.get_shape_ref()
                    builder.triples.append("\n$inter_shape_type_to_add$")
                builder.add_triple(path, "?" + v)

        if self.get_datatype() is not None:
            for v in variables:
                builder.add_datatype_filter(v, self.get_datatype(), self.get_is_pos())

        if len(variables) > 1 and or_value == 0:
            builder.add_cardinality_filter(variables)

    @staticmethod
    def generate_variables(var_generator, type_, number_of_variables):
        """Generates variable names for the SPARQL queries of the constraint."""
        vars_ = []
        if number_of_variables:
            for _ in range(number_of_variables):
                vars_.append(var_generator.generate_variable(type_))

        return vars_

    def get_variables(self):
        return self.variables

    def compute_rule_pattern_body(self):
        """
        Compute the body of the rule patterns representing the constraint.

        :return: rule pattern body of the constraint
        """
        return [(self.shapeRef, v, self.isPos) for v in self.variables] if self.shapeRef is not None else []
