__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.sparql.QueryGenerator import get_target_node_statement
from TravSHACL.utils.VariableGenerator import VariableGenerator


class XoneConstraint(Constraint):
    """Represents sh:xone over referenced node shapes.

    Phase 3B engine fix: ``XoneConstraint`` now participates in
    ``Shape.minQuery`` construction via the polymorphic
    ``participates_in_min_query`` accessor, so its ``compute_rule_pattern_body``
    shape-ref propagations reach the engine's interleave step. Engine
    saturation is correct under the conjunction-of-disjuncts pattern.

    KNOWN LIMITATION (K-02, carried forward from Phase 2C-A): the engine
    still treats disjuncts as a conjunction at the rule-pattern body level,
    not strict SHACL §4.6.4 "exactly one". A focus that satisfies two
    disjuncts is classified valid under the current engine but should be
    classified invalid under strict xone. Strict exactly-one enforcement
    requires the engine's interleave step to count satisfied disjuncts —
    out of scope for P3B, deferred until ``sh:ValidationReport`` sub-result
    emission lands (Phase 4+).

    Documented in ADR-009 (P3B engine fix and K-02 disposition) and in
    HANDOFF-phase-2c-to-phase-3.md (original deferral context). Parser
    dispatch is implemented so sh:xone does not raise
    ``NotImplementedError`` for shape-ref inners.

    Out of scope (raises ``NotImplementedError`` at parse time): atomic-
    property inners (e.g., ``sh:xone ( [sh:datatype xsd:integer] ... )``).
    """

    SOURCE_COMPONENT = "http://www.w3.org/ns/shacl#XoneConstraintComponent"

    def __init__(self, id_, shape_refs, is_pos, options, target_def=None):
        super().__init__(id_, is_pos, None, None, None, None, target_def, None, options)
        self.shapeRefs = tuple(shape_refs)
        self.min = 1
        self.max = -1
        self.variables = [VariableGenerator.get_focus_node_var()]

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        """Inject the parent shape's target-class triple so the minQuery binds ?x.

        Same engine-participation pattern as ``AndConstraint``. See K-02 in this
        class' docstring and ADR-009 for the exactly-one-semantics deferral.
        """
        if builder.target_query is not None:
            target_body = get_target_node_statement(builder.target_query).strip()
            if target_body and target_body not in builder.triples:
                builder.triples.append(target_body + ".")

    def participates_in_min_query(self) -> bool:
        """``XoneConstraint`` holds its shape-refs in ``shapeRefs`` (plural). Override
        the base accessor so the engine includes this constraint in minQuery
        construction. P3B engine fix (saturation only); strict exactly-one
        semantics deferred per K-02. See ADR-009.
        """
        return len(self.shapeRefs) > 0

    def compute_rule_pattern_body(self):
        """Propagate each disjunct shape reference to the rule-based engine.

        See class docstring re: known limitation — this propagation pattern
        gives the engine conjunction semantics, not exactly-one. Phase 3
        engine support will refine to strict sh:xone semantics.
        """
        focus_var = VariableGenerator.get_focus_node_var()
        return [(shape_ref, focus_var, self.isPos) for shape_ref in self.shapeRefs]
