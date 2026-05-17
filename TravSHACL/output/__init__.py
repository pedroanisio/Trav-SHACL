"""Output-format extensions for Trav-SHACL.

Currently provides ``serialize_validation_report`` for emitting
spec-conformant ``sh:ValidationReport`` graphs (Turtle or JSON-LD).
Future format extensions (e.g., ``cover-report.md`` snapshots, JSON-LD
profiles, statistics dumps) belong here.
"""

from TravSHACL.output.ValidationReportSerializer import serialize_validation_report

__all__ = ["serialize_validation_report"]
