__author__ = "Monica Figuera and Philipp D. Rohde"

from TravSHACL.constraints.Constraint import Constraint
from TravSHACL.utils.VariableGenerator import VariableGenerator


class XoneConstraint(Constraint):
    """Represents sh:xone over referenced node shapes.

    KNOWN LIMITATION (Phase 3+): Trav-SHACL's rule-based engine classifies
    focus nodes against each referenced shape independently. The current
    implementation propagates each disjunct via ``compute_rule_pattern_body``
    using the conjunction-of-shape-refs pattern shared with ``AndConstraint``.
    This means ``XoneConstraint`` currently behaves as a *non-strict* check:
    the engine accepts a focus when at least one disjunct matches, but does
    not enforce the SHACL §4.6.4 "exactly one" requirement at validation
    time. Strict exactly-one enforcement requires engine support for
    counting valid disjuncts in the rule-pattern saturation step —
    deferred to Phase 3 along with sh:ValidationReport sub-result emission.

    Documented in ADR-008 (sh:not architecture; sister logical constraint)
    and HANDOFF-phase-2c-to-phase-3.md (known limitations). Parser dispatch
    is implemented so sh:xone no longer raises NotImplementedError; engine
    semantics are the open work.

    Out of scope (raises ``NotImplementedError`` at parse time): atomic-
    property inners (e.g., ``sh:xone ( [sh:datatype xsd:integer] ... )``).
    """

    def __init__(self, id_, shape_refs, is_pos, options, target_def=None):
        super().__init__(id_, is_pos, None, None, None, None, target_def, None, options)
        self.shapeRefs = tuple(shape_refs)
        self.min = 1
        self.max = -1
        self.variables = [VariableGenerator.get_focus_node_var()]

    def emit_filter(self, builder, focus_var, or_value: int = 0, or_affix: int = 0, maxonly: bool = False):
        """Bind focus variable; shape-ref propagation handles engine-side classification.

        See class docstring re: known limitation around strict exactly-one
        enforcement. The BIND keeps the focus variable shape-aware in the
        constraint query, matching the AndConstraint pattern.
        """
        builder.triples.append("BIND(?" + focus_var + " AS ?" + focus_var + ")")

    def compute_rule_pattern_body(self):
        """Propagate each disjunct shape reference to the rule-based engine.

        See class docstring re: known limitation — this propagation pattern
        gives the engine conjunction semantics, not exactly-one. Phase 3
        engine support will refine to strict sh:xone semantics.
        """
        focus_var = VariableGenerator.get_focus_node_var()
        return [(shape_ref, focus_var, self.isPos) for shape_ref in self.shapeRefs]
