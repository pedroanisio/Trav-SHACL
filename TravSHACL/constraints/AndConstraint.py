__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.sparql.QueryGenerator import get_target_node_statement
from TravSHACL.utils.VariableGenerator import VariableGenerator


class AndConstraint(Constraint):
    """Represents sh:and over referenced node shapes."""

    SOURCE_COMPONENT = "http://www.w3.org/ns/shacl#AndConstraintComponent"

    def __init__(self, id_, shape_refs, is_pos, options, target_def=None):
        super().__init__(id_, is_pos, None, None, None, None, target_def, None, options)
        self.shapeRefs = tuple(shape_refs)
        self.min = 1
        self.max = -1
        self.variables = [VariableGenerator.get_focus_node_var()]

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        """Inject the parent shape's target-class triple so the minQuery binds ?x.

        Without this, the minQuery emitted for a shape whose sole min-constraint is
        sh:and would have no triple binding ?x — SPARQL would return zero rows and
        the engine's interleave step would never receive the focus-shape-ref
        propagations that ``compute_rule_pattern_body`` declared. P3B engine fix
        candidate (a): target-passthrough triple emission. See ADR-009.
        """
        if builder.target_query is not None:
            target_body = get_target_node_statement(builder.target_query).strip()
            if target_body and target_body not in builder.triples:
                builder.triples.append(target_body + ".")

    def participates_in_min_query(self) -> bool:
        """``AndConstraint`` holds its shape-refs in ``shapeRefs`` (plural), not the
        inherited ``shapeRef`` singular field. Override the base accessor so the
        engine includes this constraint in minQuery construction, letting
        ``compute_rule_pattern_body`` shape-ref propagations reach the interleave
        step. P3B engine fix; see ADR-009.
        """
        return len(self.shapeRefs) > 0

    def compute_rule_pattern_body(self):
        focus_var = VariableGenerator.get_focus_node_var()
        return [(shape_ref, focus_var, self.isPos) for shape_ref in self.shapeRefs]
