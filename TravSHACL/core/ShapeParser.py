__author__ = "Monica Figuera and Philipp D. Rohde"

import collections
import json
import logging
import os
from itertools import islice
from typing import Any
from urllib.parse import urlparse

import rdflib.term
from rdflib import Graph
from rdflib.namespace import RDF

from TravSHACL.constraints.AndConstraint import AndConstraint
from TravSHACL.constraints.ClassConstraint import ClassConstraint
from TravSHACL.constraints.ClosedConstraint import ClosedConstraint
from TravSHACL.constraints.HasValueConstraint import HasValueConstraint
from TravSHACL.constraints.InConstraint import InConstraint
from TravSHACL.constraints.LanguageInConstraint import LanguageInConstraint
from TravSHACL.constraints.MaxLengthConstraint import MaxLengthConstraint
from TravSHACL.constraints.MaxOnlyConstraint import MaxOnlyConstraint
from TravSHACL.constraints.MinLengthConstraint import MinLengthConstraint
from TravSHACL.constraints.MinOnlyConstraint import MinOnlyConstraint
from TravSHACL.constraints.NodeKindConstraint import NodeKindConstraint
from TravSHACL.constraints.NotConstraint import NotConstraint
from TravSHACL.constraints.PairDisjointConstraint import PairDisjointConstraint
from TravSHACL.constraints.PairEqualsConstraint import PairEqualsConstraint
from TravSHACL.constraints.PairLessThanConstraint import PairLessThanConstraint
from TravSHACL.constraints.PairLessThanOrEqualsConstraint import PairLessThanOrEqualsConstraint
from TravSHACL.constraints.PatternConstraint import PatternConstraint
from TravSHACL.constraints.QualifiedValueShapeConstraint import QualifiedValueShapeConstraint
from TravSHACL.constraints.RangeMaxExclusiveConstraint import RangeMaxExclusiveConstraint
from TravSHACL.constraints.RangeMaxInclusiveConstraint import RangeMaxInclusiveConstraint
from TravSHACL.constraints.RangeMinExclusiveConstraint import RangeMinExclusiveConstraint
from TravSHACL.constraints.RangeMinInclusiveConstraint import RangeMinInclusiveConstraint
from TravSHACL.constraints.SPARQLConstraint import SPARQLConstraint
from TravSHACL.constraints.UniqueLangConstraint import UniqueLangConstraint
from TravSHACL.constraints.XoneConstraint import XoneConstraint
from TravSHACL.core.Path import Alternative, Inverse, OneOrMore, PathExpression, Predicate, Sequence, ZeroOrMore, ZeroOrOne
from TravSHACL.core.Shape import Shape
from TravSHACL.utils.VariableGenerator import VariableGenerator

NAMESPACE_SHACL = "http://www.w3.org/ns/shacl#"
NAMESPACE_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NAMESPACE_RDFS = "http://www.w3.org/2000/01/rdf-schema#"

SH_NODE_SHAPE = NAMESPACE_SHACL + "NodeShape"
SH_PROPERTY_SHAPE = NAMESPACE_SHACL + "PropertyShape"

CONSTRAINT_DISPATCH = {
    NAMESPACE_SHACL + "path": "path",
    NAMESPACE_SHACL + "minCount": "min",
    NAMESPACE_SHACL + "maxCount": "max",
    NAMESPACE_SHACL + "qualifiedMinCount": "qualifiedMin",
    NAMESPACE_SHACL + "qualifiedMaxCount": "qualifiedMax",
    NAMESPACE_SHACL + "datatype": "datatype",
    NAMESPACE_SHACL + "qualifiedValueShape": "qualifiedShape",
    NAMESPACE_SHACL + "qualifiedValueShapesDisjoint": "qualifiedDisjoint",
    NAMESPACE_SHACL + "node": "shape",
    NAMESPACE_SHACL + "value": "value",
    NAMESPACE_SHACL + "not": "negated",
    NAMESPACE_SHACL + "and": "and",
    NAMESPACE_SHACL + "xone": "xone",
    NAMESPACE_SHACL + "closed": "closed",
    NAMESPACE_SHACL + "ignoredProperties": "ignoredProperties",
    NAMESPACE_SHACL + "hasValue": "hasValue",
    NAMESPACE_SHACL + "in": "in",
    NAMESPACE_SHACL + "class": "class",
    NAMESPACE_SHACL + "nodeKind": "nodeKind",
    NAMESPACE_SHACL + "minInclusive": "minInclusive",
    NAMESPACE_SHACL + "minExclusive": "minExclusive",
    NAMESPACE_SHACL + "maxInclusive": "maxInclusive",
    NAMESPACE_SHACL + "maxExclusive": "maxExclusive",
    NAMESPACE_SHACL + "minLength": "minLength",
    NAMESPACE_SHACL + "maxLength": "maxLength",
    NAMESPACE_SHACL + "pattern": "pattern",
    NAMESPACE_SHACL + "languageIn": "languageIn",
    NAMESPACE_SHACL + "uniqueLang": "uniqueLang",
    NAMESPACE_SHACL + "equals": "equals",
    NAMESPACE_SHACL + "disjoint": "disjoint",
    NAMESPACE_SHACL + "lessThan": "lessThan",
    NAMESPACE_SHACL + "lessThanOrEquals": "lessThanOrEquals",
}

METADATA_DISPATCH = {
    NAMESPACE_SHACL + "severity": "severity",
    NAMESPACE_SHACL + "name": "name",
    NAMESPACE_SHACL + "description": "description",
    NAMESPACE_SHACL + "group": "group",
    NAMESPACE_SHACL + "order": "order",
    NAMESPACE_SHACL + "defaultValue": "defaultValue",
}

IGNORED_CONSTRAINT_IRIS = {
    NAMESPACE_RDF + "type",
    NAMESPACE_SHACL + "targetClass",
    NAMESPACE_SHACL + "targetNode",
    NAMESPACE_SHACL + "targetSubjectsOf",
    NAMESPACE_SHACL + "targetObjectsOf",
    NAMESPACE_SHACL + "targetQuery",
}

QUERY_TARGET_QUERY = """SELECT ?query WHERE {{
  <{shape}> <http://www.w3.org/ns/shacl#targetQuery> ?query .
}}"""

log = logging.getLogger(__name__)


def _row_value(row: Any, index: int) -> Any:
    return row[index]


class ShapeParser:
    """Used for parsing shape definitions from files to the internal representation."""

    def __init__(self, ignore_errors=False):
        """Initialize the shape parser.

        :param ignore_errors: whether to ignore parsing errors, i.e., logging a warning instead of throwing an exception
        """
        self.ignore_errors = ignore_errors

    def parse_shapes_from_dir(self, path, shape_format, use_selective_queries, max_split_size, order_by_in_queries):
        """
        Parses all files of a certain file extension in the directory.
        It assumes that each file represents one SHACL shape.

        :param path: the path to the directory that stores the shapes files
        :param shape_format: the representation format of the shape definitions
        :param use_selective_queries: indicates whether selective queries are used
        :param max_split_size: maximum number of instances per query
        :param order_by_in_queries: indicates whether to use the ORDER BY clause
        :return: list of Shapes parsed from the files
        """
        file_extension = self.get_file_extension(shape_format)
        files_abs_paths = []

        # r=root, f=files, ignoring subdirectories
        for r, _, f in os.walk(path):
            for file in f:
                file_path = os.path.join(r, file)
                if file_extension == os.path.splitext(file_path)[1].lower():
                    files_abs_paths.append(file_path)

        if not files_abs_paths:
            raise FileNotFoundError(path + " does not contain any shapes of the format " + shape_format)

        if shape_format == "JSON":
            return [
                self.parse_json(
                    path=p,
                    use_selective_queries=use_selective_queries,
                    max_split_size=max_split_size,
                    order_by_in_queries=order_by_in_queries,
                )
                for p in files_abs_paths
            ]
        if shape_format == "SHACL":
            shapes = []
            [
                shapes.extend(
                    self.parse_ttl(
                        shapes_graph=Graph().parse(p),
                        use_selective_queries=use_selective_queries,
                        max_split_size=max_split_size,
                        order_by_in_queries=order_by_in_queries,
                    )
                )
                for p in files_abs_paths
            ]
            return shapes
        else:
            print("Unexpected format: " + shape_format)

    @staticmethod
    def get_file_extension(shape_format):
        if shape_format == "SHACL":
            return ".ttl"
        else:
            return ".json"  # dot added for convenience

    def parse_json(self, path, use_selective_queries, max_split_size, order_by_in_queries):
        """
        Parses a particular file and converts its content into the internal representation of a SHACL shape.

        :param path: the path to the shapes file
        :param use_selective_queries: indicates whether selective queries are used
        :param max_split_size: maximum number of instances per query
        :param order_by_in_queries: indicates whether to use the ORDER BY clause
        :return: Shape object representing the parsed SHACL shape
        """
        target_query = None
        target_type = None

        with open(path) as file:
            obj = json.load(file)
        target_def = obj.get("targetDef")
        name = obj["name"]
        shape_kind = obj.get("shapeKind", "NodeShape")
        shape_metadata = self.parse_json_metadata(obj)
        id_ = name + "_d1"  # str(i + 1) but there is only one set of conjunctions
        constraints = self.parse_constraints(obj["constraintDef"]["conjunctions"], target_def, id_)

        include_sparql_prefixes = self.abbreviated_syntax_used(constraints)
        prefixes = None
        if "prefix" in obj:
            prefixes = obj["prefix"]
        referenced_shapes = self.shape_references(obj["constraintDef"]["conjunctions"][0])
        valid_flag = [False]  # for json files, the 'or' operations can be implemented starting from here

        if target_def is not None:
            target_query = target_def["query"]

            target_def_copy = target_def.copy()
            del target_def_copy["query"]
            target_type = list(target_def_copy.keys())[0]

            if urlparse(target_def[target_type]).netloc != "":  # if the target node is a url, add '<>' to it
                target_def = "<" + target_def[target_type] + ">"
            else:
                target_def = target_def[target_type]

        return Shape(
            name,
            target_def,
            target_type,
            target_query,
            constraints,
            id_,
            referenced_shapes,
            use_selective_queries,
            max_split_size,
            order_by_in_queries,
            include_sparql_prefixes,
            valid_flag,
            prefixes,
            shape_kind=shape_kind,
            **shape_metadata,
        )

    def parse_ttl(self, shapes_graph: Graph, use_selective_queries, max_split_size, order_by_in_queries):
        """
        Parses a particular file and converts its content into the internal representation of a SHACL shape.

        :param shapes_graph: RDFlib graph containing the shapes
        :param use_selective_queries: indicates whether selective queries are used
        :param max_split_size: maximum number of instances per query
        :param order_by_in_queries: indicates whether to use the ORDER BY clause
        :return: Shape object representing the parsed SHACL shape
        """
        queries = self.get_QUERY()
        shapes = []

        shape_entries = [(str(_row_value(row, 0)), str(_row_value(row, 1))) for row in shapes_graph.query(queries[0])]

        for name, shape_kind in shape_entries:
            id_ = name + "_d1"  # str(i + 1) but there is only one set of conjunctions
            shape_metadata = self.parse_shape_metadata(shapes_graph, name, queries[9])

            # to get the target_ref and target_type
            target_def = None
            target_type = None
            if len(shapes_graph.query(queries[1].format(shape=name))) != 0:
                for res in shapes_graph.query(queries[1].format(shape=name)):
                    target_def = str(_row_value(res, 0))
                    target_type = "class"
                    break
            elif len(shapes_graph.query(queries[2].format(shape=name))) != 0:
                for res in shapes_graph.query(queries[2].format(shape=name)):
                    target_def = str(_row_value(res, 0))
                    target_type = "node"
                    break
            elif len(shapes_graph.query(queries[10].format(shape=name))) != 0:
                for res in shapes_graph.query(queries[10].format(shape=name)):
                    target_def = str(_row_value(res, 0))
                    target_type = "subjectsOf"
                    break
            elif len(shapes_graph.query(queries[11].format(shape=name))) != 0:
                for res in shapes_graph.query(queries[11].format(shape=name)):
                    target_def = str(_row_value(res, 0))
                    target_type = "objectsOf"
                    break
            elif len(shapes_graph.query(queries[12].format(shape=name))) != 0:
                target_def = name
                target_type = "implicitClass"

            target_query = None
            if target_def is not None and target_type in {"class", "implicitClass"}:
                for res in shapes_graph.query(QUERY_TARGET_QUERY.format(shape=name)):
                    target_query = str(_row_value(res, 0))
                if target_query is None:
                    target_query = "SELECT ?x WHERE { ?x a " + self.sparql_term(target_def) + " }"
                    target_def = self.sparql_term(target_def)
            elif target_def is not None and target_type == "subjectsOf":
                target_def = self.sparql_term(target_def)
                target_query = "SELECT ?x WHERE { ?x " + target_def + " ?target }"
            elif target_def is not None and target_type == "objectsOf":
                target_def = self.sparql_term(target_def)
                target_query = "SELECT ?x WHERE { ?target " + target_def + " ?x }"

            cons_dict = self.parse_all_const(
                shapes_graph, name=name, target_def=target_def, target_type=target_type, query=queries
            )
            const_array = list(cons_dict.values())  # change the format to an array

            # valid_flag = [entry['flag'] for entry in const_array if entry['flag']]
            valid_flag = []
            for entry in const_array:
                if "flag" in entry:
                    valid_flag.append(entry["flag"])

            constraints = self.parse_constraints_ttl(const_array, target_def, id_)
            include_sparql_prefixes = self.abbreviated_syntax_used(constraints)
            prefixes = None
            referenced_shapes = self.shape_references(const_array)

            # helps to navigate the shape.__compute_target_queries function
            referenced_shape = {
                self.sparql_term(key): self.sparql_term(referenced_shapes[key]) for key in referenced_shapes
            }

            # to helps to navigate the ShapeSchema.compute_edges function
            name_ = "<" + name + ">" if urlparse(name).netloc != "" else name

            shapes.append(
                Shape(
                    name_,
                    target_def,
                    target_type,
                    target_query,
                    constraints,
                    id_,
                    referenced_shape,
                    use_selective_queries,
                    max_split_size,
                    order_by_in_queries,
                    include_sparql_prefixes,
                    valid_flag,
                    prefixes,
                    shape_kind=shape_kind,
                    **shape_metadata,
                )
            )

        return shapes

    @staticmethod
    def parse_json_metadata(obj):
        return {
            "deactivated": ShapeParser.parse_bool(obj.get("deactivated", False)),
            "severity": obj.get("severity"),
            "name": obj.get("displayName") or obj.get("label"),
            "description": obj.get("description"),
            "group": obj.get("group"),
            "order": obj.get("order"),
            "default_value": obj.get("defaultValue"),
        }

    @staticmethod
    def parse_bool(value):
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"true", "1"}

    @staticmethod
    def parse_shape_metadata(shapes_graph, shape, query):
        metadata = {
            "deactivated": False,
            "severity": None,
            "name": None,
            "description": None,
            "group": None,
            "order": None,
            "default_value": None,
        }
        for result in shapes_graph.query(query.format(shape=shape)):
            predicate = str(result["p"])
            value = str(result["o"])
            if predicate == NAMESPACE_SHACL + "deactivated":
                metadata["deactivated"] = ShapeParser.parse_bool(value)
            elif predicate == NAMESPACE_SHACL + "defaultValue":
                metadata["default_value"] = value
            else:
                key = METADATA_DISPATCH.get(predicate)
                if key is not None:
                    metadata[key] = value
        return metadata

    @staticmethod
    def sparql_term(value):
        if value is None:
            return None
        value = str(value)
        if value.startswith("<") and value.endswith(">"):
            return value
        if urlparse(value).netloc != "":
            return "<" + value + ">"
        return value

    @staticmethod
    def sparql_literal(value):
        if isinstance(value, rdflib.term.Literal):
            lexical = json.dumps(str(value))
            if value.language:
                return lexical + "@" + value.language
            if value.datatype:
                return lexical + "^^<" + str(value.datatype) + ">"
            return lexical
        if isinstance(value, rdflib.term.URIRef):
            return "<" + str(value) + ">"
        return str(value)

    @staticmethod
    def constraint_value(predicate, value):
        literal_predicates = {
            NAMESPACE_SHACL + "minInclusive",
            NAMESPACE_SHACL + "minExclusive",
            NAMESPACE_SHACL + "maxInclusive",
            NAMESPACE_SHACL + "maxExclusive",
        }
        quoted_string_predicates = {NAMESPACE_SHACL + "pattern", NAMESPACE_SHACL + "flags"}

        if predicate in literal_predicates:
            return ShapeParser.sparql_literal(value)
        if predicate == NAMESPACE_SHACL + "hasValue" and isinstance(value, rdflib.term.Literal):
            return ShapeParser.sparql_literal(value)
        if predicate in quoted_string_predicates:
            return json.dumps(str(value))
        return str(value)

    @staticmethod
    def abbreviated_syntax_used(constraints):
        """
        Run after parsingConstraints.
        Returns false if the constraints' predicates are using absolute paths instead of abbreviated ones
        :param constraints: all shape constraints
        :return: True if prefix notation is used, False otherwise
        """
        for c in constraints:
            path = c.path_sparql()
            if path is not None and (path.startswith("<") and path.endswith(">")):
                return False
        return True

    @staticmethod
    def shape_references(constraints):
        """
        Gets the shapes referenced by the given constraints.

        :param constraints: the constraints to get the referenced shapes for
        :return: Python dictionary with the referenced shapes and the path referencing the shape
        """
        return {
            c.get("shape"): PathExpression.from_string(c.get("path")).to_sparql()
            for c in constraints
            if c.get("shape") is not None
        }

    @staticmethod
    def chunks(datei, SIZE):
        """
        Break down list of input (dictionaries) into individual dictionaries

        :param datei: list of input to be broken down
        :param SIZE: tells the length or size for each output
        :return: inputs divided in len(SIZE)
        """
        it = iter(datei)
        for _ in range(0, len(datei), SIZE):
            yield {k: datei[k] for k in islice(it, SIZE)}

    @staticmethod
    def get_QUERY():
        QUERY_SHAPES = """SELECT DISTINCT ?shape ?shape_kind WHERE {
            {
                ?shape a <http://www.w3.org/ns/shacl#NodeShape> .
                BIND("NodeShape" AS ?shape_kind)
            } UNION {
                ?shape a <http://www.w3.org/ns/shacl#PropertyShape> .
                BIND("PropertyShape" AS ?shape_kind)
            }
            } ORDER BY ?shape"""

        QUERY_TARGET_1 = """SELECT ?target WHERE {{
            <{shape}> <http://www.w3.org/ns/shacl#targetClass> ?target .
            }}
                """

        QUERY_TARGET_2 = """SELECT ?target WHERE {{
                    <{shape}> <http://www.w3.org/ns/shacl#targetNode> ?target .
                    }}
                        """

        QUERY_TARGET_SUBJECTS_OF = """SELECT ?target WHERE {{
                    <{shape}> <http://www.w3.org/ns/shacl#targetSubjectsOf> ?target .
                    }}
                        """

        QUERY_TARGET_OBJECTS_OF = """SELECT ?target WHERE {{
                    <{shape}> <http://www.w3.org/ns/shacl#targetObjectsOf> ?target .
                    }}
                        """

        QUERY_IMPLICIT_CLASS = """SELECT ?class WHERE {{
                    <{shape}> a <http://www.w3.org/2000/01/rdf-schema#Class> .
                    BIND(<{shape}> AS ?class)
                    }}
                        """

        QUERY_CONSTRAINTS = """SELECT ?constraint WHERE {{
          {{
              <{shape}> a <http://www.w3.org/ns/shacl#NodeShape> .
              <{shape}> <http://www.w3.org/ns/shacl#property> ?constraint .
          }} UNION {{
              <{shape}> a <http://www.w3.org/ns/shacl#PropertyShape> .
              BIND(<{shape}> AS ?constraint)
          }}
        }}
        """

        QUERY_CONSTRAINT_DETAILS = """SELECT ?p ?o WHERE {{
            {{
                ?s ?p ?o .
                FILTER( str(?s) = "{constraint}" )
            }} UNION {{
                ?s <http://www.w3.org/ns/shacl#path>/<http://www.w3.org/ns/shacl#inversePath> ?o .
                BIND(<http://www.w3.org/ns/shacl#path> AS ?p)
                BIND(CONCAT('^', str(?o)) AS ?o)
                FILTER( str(?s) = "{constraint}" )
            }} UNION {{
                SELECT ?p (group_concat(?o;separator="/") as ?o) WHERE {{
                    ?s <http://www.w3.org/ns/shacl#path> ?pathList .
                    FILTER( str(?s) = "{constraint}" )
                    BIND(<http://www.w3.org/ns/shacl#path> AS ?p)
                    ?pathList rdf:rest*/rdf:first ?o .
                    BIND(CONCAT('<', str(?o), '>') AS ?o)
                }} GROUP BY ?s
            }}
        }}"""

        QUERY_QVS_REF_1 = """SELECT ?shape_ref WHERE {{
              ?s <http://www.w3.org/ns/shacl#node> ?shape_ref .
              FILTER ( str(?s) = "{qvs}" )
            }}"""

        QUERY_QVS_REF_2 = """SELECT ?shape_ref WHERE {{
                  ?s <http://www.w3.org/ns/shacl#value> ?shape_ref .
                  FILTER ( str(?s) = "{qvs}" )
                }}"""

        QUERY_SPARQL_CONSTRAINTS = """SELECT ?constraint ?query WHERE {{
          <{shape}> a <http://www.w3.org/ns/shacl#NodeShape> .
          <{shape}> <http://www.w3.org/ns/shacl#sparql> ?constraint .
          ?constraint <http://www.w3.org/ns/shacl#select> ?query .
        }}
        """

        QUERY_OR = """SELECT ?constraint WHERE {{
                                  <{shape}> a <http://www.w3.org/ns/shacl#NodeShape> .
                                  <{shape}> <http://www.w3.org/ns/shacl#or> ?constraint .
                                }}
                                """
        QUERY_SHAPE_METADATA = """SELECT ?p ?o WHERE {{
            <{shape}> ?p ?o .
            FILTER(?p IN (
                <http://www.w3.org/ns/shacl#deactivated>,
                <http://www.w3.org/ns/shacl#severity>,
                <http://www.w3.org/ns/shacl#name>,
                <http://www.w3.org/ns/shacl#description>,
                <http://www.w3.org/ns/shacl#group>,
                <http://www.w3.org/ns/shacl#order>,
                <http://www.w3.org/ns/shacl#defaultValue>
            ))
        }}"""
        return (
            QUERY_SHAPES,
            QUERY_TARGET_1,
            QUERY_TARGET_2,
            QUERY_CONSTRAINTS,
            QUERY_CONSTRAINT_DETAILS,
            QUERY_QVS_REF_1,
            QUERY_QVS_REF_2,
            QUERY_SPARQL_CONSTRAINTS,
            QUERY_OR,
            QUERY_SHAPE_METADATA,
            QUERY_TARGET_SUBJECTS_OF,
            QUERY_TARGET_OBJECTS_OF,
            QUERY_IMPLICIT_CLASS,
        )

    def get_res(self, filename, name, query):
        """

        :param query: List of queries
        :param name: name of the Shape
        :param filename: shape file in ttl format
        :return: valid response from query execution
        """
        exp_dict = collections.defaultdict(list)
        self._append_shape_level_constraints(filename, name, exp_dict)
        if filename.query(query[3].format(shape=name)):
            for constraint in filename.query(query[3].format(shape=name)):
                constraint_id = constraint[0]

                for detail in filename.query(query[4].format(constraint=constraint_id)):
                    detail_dict = detail.asdict()
                    predicate = str(detail_dict["p"])
                    obj = detail_dict["o"]

                    if isinstance(obj, rdflib.term.BNode) and predicate == NAMESPACE_SHACL + "path":
                        exp_dict[str(constraint_id)].append([predicate, self.parse_path_node(filename, obj)])
                    elif isinstance(obj, rdflib.term.BNode) and predicate == NAMESPACE_SHACL + "languageIn":
                        languages = [json.dumps(str(item)) for item in filename.items(obj)]
                        exp_dict[str(constraint_id)].append([predicate, languages])
                    elif isinstance(obj, rdflib.term.BNode) and predicate == NAMESPACE_SHACL + "in":
                        values = [self.sparql_literal(item) for item in filename.items(obj)]
                        exp_dict[str(constraint_id)].append([predicate, values])
                    elif isinstance(obj, rdflib.term.BNode) and predicate == NAMESPACE_SHACL + "qualifiedValueShape":
                        exp_dict[str(constraint_id)].append([predicate, self.parse_shape_expression(filename, obj)])
                    elif isinstance(obj, rdflib.term.BNode) and predicate == NAMESPACE_SHACL + "not":
                        exp_dict[str(constraint_id)].append([predicate, self.parse_property_shape(filename, obj)])
                    elif isinstance(obj, rdflib.term.BNode):
                        qv_type = detail_dict["p"]
                        qvs = obj
                        if len(filename.query(query[5].format(qvs=qvs))) != 0:
                            dict_1 = None
                            for shape_ref in filename.query(query[5].format(qvs=qvs)):
                                dict_1 = [qv_type, str(shape_ref.asdict()["shape_ref"])]
                            if dict_1 is not None:
                                exp_dict[str(constraint_id)].append(dict_1.copy())
                            else:
                                if self.ignore_errors:
                                    log.warning("There was an unsupported constraint, skipping it...")
                                else:
                                    raise NotImplementedError(
                                        "It seems you are using an unsupported feature. Please, check your shape schema."
                                    )
                        else:
                            dict_1 = None
                            for shape_ref in filename.query(query[6].format(qvs=qvs)):
                                dict_1 = [qv_type, ["value", str(shape_ref.asdict()["shape_ref"])]]
                            if dict_1 is not None:
                                exp_dict[str(constraint_id)].append(dict_1.copy())
                            else:
                                if self.ignore_errors:
                                    log.warning("There was an unsupported constraint, skipping it...")
                                else:
                                    raise NotImplementedError(
                                        "It seems you are using an unsupported feature. Please, check your shape schema."
                                    )
                    else:
                        # detail_dict = detail.asdict()
                        dict_2 = [predicate, self.constraint_value(predicate, obj)]
                        exp_dict[str(constraint_id)].append(dict_2.copy())

        if filename.query(query[8].format(shape=name)):
            for constraint in filename.query(query[8].format(shape=name)):
                constraint_id = filename.items(constraint[0])
                dict_or = collections.defaultdict(list)
                for item in constraint_id:
                    for detail in filename.query(query[4].format(constraint=item.toPython())):
                        detail_dict = detail.asdict()
                        dict_3 = [
                            str(detail_dict["p"]),
                            self.constraint_value(str(detail_dict["p"]), detail_dict["o"]),
                        ]
                        dict_or[str(item)].append(dict_3.copy())
                exp_dict[str(constraint_id)].append(dict_or.copy())

        return exp_dict

    def _append_shape_level_constraints(self, filename, name, exp_dict):
        subject = rdflib.term.URIRef(name)
        direct = []
        for predicate, obj in filename.predicate_objects(subject):
            predicate = str(predicate)
            if predicate not in CONSTRAINT_DISPATCH:
                continue
            if predicate in {NAMESPACE_SHACL + "path", NAMESPACE_SHACL + "node", NAMESPACE_SHACL + "value"}:
                continue
            if predicate == NAMESPACE_SHACL + "closed":
                direct.append([predicate, self.parse_bool(obj)])
            elif predicate == NAMESPACE_SHACL + "ignoredProperties" and isinstance(obj, rdflib.term.BNode):
                direct.append([predicate, [self.sparql_term(item) for item in filename.items(obj)]])
            elif predicate in {NAMESPACE_SHACL + "and", NAMESPACE_SHACL + "xone"}:
                direct.append([predicate, [self.parse_shape_expression(filename, item) for item in filename.items(obj)]])
            elif predicate == NAMESPACE_SHACL + "not" and isinstance(obj, rdflib.term.BNode):
                direct.append([predicate, self.parse_property_shape(filename, obj)])
            elif predicate == NAMESPACE_SHACL + "not":
                if self.ignore_errors:
                    log.warning("Unsupported SHACL shape-ref sh:not %s; skipping it...", obj)
                else:
                    raise NotImplementedError("Shape-reference sh:not is not implemented")
        if direct:
            exp_dict[name + "#shape-level"].extend(direct)

    def parse_shape_expression(self, filename, node):
        node_ref = filename.value(node, rdflib.term.URIRef(NAMESPACE_SHACL + "node"))
        if node_ref is not None:
            return {"shape": self.sparql_term(node_ref)}

        class_ref = filename.value(node, rdflib.term.URIRef(NAMESPACE_SHACL + "class"))
        if class_ref is not None:
            return {"class": self.sparql_term(class_ref)}

        property_ref = filename.value(node, rdflib.term.URIRef(NAMESPACE_SHACL + "property"))
        if property_ref is not None:
            return self.parse_property_shape(filename, property_ref)

        if not isinstance(node, rdflib.term.BNode):
            return {"shape": self.sparql_term(node)}

        if self.ignore_errors:
            log.warning("Unsupported SHACL shape expression %s; skipping it...", node)
            return {}
        raise NotImplementedError("Unsupported SHACL shape expression: " + str(node))

    def parse_property_shape(self, filename, node):
        parsed = {}
        for predicate, obj in filename.predicate_objects(node):
            predicate = str(predicate)
            if predicate == NAMESPACE_SHACL + "path":
                parsed["path"] = self.parse_path_node(filename, obj)
            elif predicate == NAMESPACE_SHACL + "in" and isinstance(obj, rdflib.term.BNode):
                parsed["in"] = [self.sparql_literal(item) for item in filename.items(obj)]
            elif predicate == NAMESPACE_SHACL + "languageIn" and isinstance(obj, rdflib.term.BNode):
                parsed["languageIn"] = [json.dumps(str(item)) for item in filename.items(obj)]
            elif predicate == NAMESPACE_SHACL + "qualifiedValueShape" and isinstance(obj, rdflib.term.BNode):
                parsed["qualifiedShape"] = self.parse_shape_expression(filename, obj)
            elif predicate == NAMESPACE_SHACL + "not" and isinstance(obj, rdflib.term.BNode):
                parsed["negated"] = self.parse_property_shape(filename, obj)
            else:
                key = CONSTRAINT_DISPATCH.get(predicate)
                if key is not None:
                    parsed[key] = self.constraint_value(predicate, obj)
                elif predicate not in IGNORED_CONSTRAINT_IRIS and not self.ignore_errors:
                    raise NotImplementedError("Unsupported SHACL constraint IRI: " + predicate)
        return parsed

    def parse_path_node(self, filename, node):
        if not isinstance(node, rdflib.term.BNode):
            return PathExpression.from_string(self.sparql_term(node))

        inverse = filename.value(node, rdflib.term.URIRef(NAMESPACE_SHACL + "inversePath"))
        if inverse is not None:
            return Inverse(self.parse_path_node(filename, inverse))

        alternative = filename.value(node, rdflib.term.URIRef(NAMESPACE_SHACL + "alternativePath"))
        if alternative is not None:
            return Alternative(self.parse_path_node(filename, item) for item in filename.items(alternative))

        zero_or_more = filename.value(node, rdflib.term.URIRef(NAMESPACE_SHACL + "zeroOrMorePath"))
        if zero_or_more is not None:
            return ZeroOrMore(self.parse_path_node(filename, zero_or_more))

        one_or_more = filename.value(node, rdflib.term.URIRef(NAMESPACE_SHACL + "oneOrMorePath"))
        if one_or_more is not None:
            return OneOrMore(self.parse_path_node(filename, one_or_more))

        zero_or_one = filename.value(node, rdflib.term.URIRef(NAMESPACE_SHACL + "zeroOrOnePath"))
        if zero_or_one is not None:
            return ZeroOrOne(self.parse_path_node(filename, zero_or_one))

        first = filename.value(node, RDF.first)
        if first is not None:
            return Sequence(self.parse_path_node(filename, item) for item in filename.items(node))

        if self.ignore_errors:
            log.warning("Unsupported SHACL path expression %s; skipping it...", node)
            return Predicate(str(node))
        raise NotImplementedError("Unsupported SHACL path expression: " + str(node))

    def parse_all_const(self, filename, name, target_def, target_type, query):
        """

        :param query: List of queries
        :param name: name of the shape
        :param target_type: indicates the target type of the shape, e.g., class or node
        :param target_def: target definition of the shape
        :param filename: file path
        :return: all constraints belonging to the shape
        """
        cons_dict = self.get_res(filename, name, query)
        trav_dict = {}
        exp_dict = {}

        trav_dict["name"] = name
        trav_dict["target_def"] = target_def
        trav_dict["target_type"] = target_type

        # SPARQL constraints first
        for result in filename.query(query[7].format(shape=name)):
            trav_dict["sparql"] = result["query"].toPython()
            exp_dict[str(result["constraint"].toPython())] = trav_dict.copy()

        for item in self.chunks(dict(cons_dict.items()), 1):
            for dk, dv in item.items():
                if type(dk) is not tuple:
                    trav_dict["min"] = None
                    trav_dict["max"] = None
                    trav_dict["qualifiedMin"] = None
                    trav_dict["qualifiedMax"] = None
                    trav_dict["qualifiedShape"] = None
                    trav_dict["qualifiedDisjoint"] = None
                    trav_dict["value"] = None
                    trav_dict["hasValue"] = None
                    trav_dict["in"] = None
                    trav_dict["path"] = None
                    trav_dict["shape"] = None
                    trav_dict["datatype"] = None
                    trav_dict["negated"] = None
                    trav_dict["and"] = None
                    trav_dict["xone"] = None
                    trav_dict["closed"] = None
                    trav_dict["ignoredProperties"] = []
                    trav_dict["class"] = None
                    trav_dict["nodeKind"] = None
                    trav_dict["minInclusive"] = None
                    trav_dict["minExclusive"] = None
                    trav_dict["maxInclusive"] = None
                    trav_dict["maxExclusive"] = None
                    trav_dict["minLength"] = None
                    trav_dict["maxLength"] = None
                    trav_dict["pattern"] = None
                    trav_dict["flags"] = None
                    trav_dict["languageIn"] = None
                    trav_dict["uniqueLang"] = None
                    trav_dict["equals"] = None
                    trav_dict["disjoint"] = None
                    trav_dict["lessThan"] = None
                    trav_dict["lessThanOrEquals"] = None
                    trav_dict["or"] = {}
                    trav_dict["flag"] = False
                    trav_dict["sparql"] = None

                    if "Graph.items" not in dk:
                        for i in dv:
                            self.dispatch_constraint_entry(trav_dict, str(i[0]), i[1])

                    else:
                        trav_dict["flag"] = True
                        for options in dv:
                            for i_or, j_or in options.items():
                                trav_dict["or"][i_or] = {}
                                for j_sub in j_or:
                                    self.dispatch_constraint_entry(trav_dict["or"][i_or], str(j_sub[0]), j_sub[1])

                exp_dict[str(dk)] = trav_dict.copy()
        self._populate_closed_allowed_paths(exp_dict)
        return exp_dict

    @staticmethod
    def _populate_closed_allowed_paths(exp_dict):
        allowed_paths = [
            entry.get("path")
            for key, entry in exp_dict.items()
            if "#shape-level" not in key and entry.get("path") is not None
        ]
        for entry in exp_dict.values():
            if entry.get("closed"):
                entry["allowedPaths"] = allowed_paths

    def dispatch_constraint_entry(self, trav_dict, predicate, value):
        if predicate == NAMESPACE_SHACL + "flags":
            trav_dict["flags"] = value
            return

        key = CONSTRAINT_DISPATCH.get(predicate)
        if key is not None:
            trav_dict[key] = value
            return

        metadata_key = METADATA_DISPATCH.get(predicate)
        if metadata_key is not None:
            trav_dict[metadata_key] = value
            return

        if predicate in IGNORED_CONSTRAINT_IRIS:
            return

        if self.ignore_errors:
            log.warning("Unsupported SHACL constraint IRI %s; skipping it...", predicate)
        else:
            raise NotImplementedError("Unsupported SHACL constraint IRI: " + predicate)

    @staticmethod
    def apply_constraint_metadata(constraints, obj):
        for constraint in constraints:
            constraint.severity = obj.get("severity")
            constraint.name = obj.get("name")
            constraint.description = obj.get("description")
            constraint.group = obj.get("group")
            constraint.order = obj.get("order")
            constraint.defaultValue = obj.get("defaultValue")
        return constraints

    def parse_constraints(self, array, target_def, constraints_id):
        """
        Parses all constraints of a shape.

        :param array: list of constraints belonging to the shape
        :param target_def: the target definition of the shape
        :param constraints_id: suffix for the constraint IDs
        :return: list of constraints in internal constraint representation
        """
        var_generator = VariableGenerator()
        constraints = []
        options = None
        [
            constraints.extend(
                self.parse_constraint(
                    var_generator, array[0][i], constraints_id + "_c" + str(i + 1), target_def, options
                )
            )
            for i in range(len(array[0]))
        ]
        return constraints

    def parse_constraints_ttl(self, array, target_def, constraints_id):
        """
        Parses all constraints of a shape.

        :param array: list of constraints belonging to the shape
        :param target_def: the target definition of the shape
        :param constraints_id: suffix for the constraint IDs
        :return: list of constraints in internal constraint representation
        """
        var_generator = VariableGenerator()
        constraints = []

        for i, constraint in enumerate(array):
            if constraint.get("flag"):
                or_constraints = []
                for key in constraint["or"]:
                    sub_constraint = constraint["or"][key]
                    or_constraints.extend(
                        self.parse_constraint(
                            var_generator, sub_constraint, constraints_id + "_c" + str(i + 1), target_def, None
                        )
                    )
                constraints.extend(
                    self.parse_constraint(
                        var_generator, constraint, constraints_id + "_c" + str(i + 1), target_def, or_constraints
                    )
                )
            else:
                constraints.extend(
                    self.parse_constraint(
                        var_generator, constraint, constraints_id + "_c" + str(i + 1), target_def, None
                    )
                )

        return constraints

    def parse_constraint(self, var_generator, obj, id_, target_def, options=None):
        """
        Parses one constraint to the internal representation.

        :param var_generator: reference to the VariableGenerator instance for variable generation for SPARQL queries
        :param obj: the constraint in its original representation
        :param id_: suffix for the constraint ID
        :param target_def: the target definition of the associated shape
        :param options: contains Constraints for or_operation
        :return: constraint in internal representation
        """
        min_ = obj.get("min")
        max_ = obj.get("max")
        qualified_min = obj.get("qualifiedMin")
        qualified_max = obj.get("qualifiedMax")
        qualified_shape = obj.get("qualifiedShape")
        shape_ref = obj.get("shape")
        datatype = obj.get("datatype")
        value = obj.get("value")
        has_value = obj.get("hasValue")
        in_values = obj.get("in")
        path = obj.get("path")
        negated = obj.get("negated")
        and_ = obj.get("and")
        xone = obj.get("xone")
        closed = obj.get("closed")
        query = obj.get("sparql")

        if isinstance(path, PathExpression):
            is_inverse_path = False
        elif path is not None and str(path).startswith("^"):
            is_inverse_path = True
            path = str(path)[1:]
        else:
            is_inverse_path = False

        o_min = None if (min_ is None) else int(min_)
        o_max = None if (max_ is None) else int(max_)
        o_shape_ref = None if (shape_ref is None) else str(shape_ref)
        o_datatype = None if (datatype is None) else str(datatype)
        o_value = None if (value is None) else str(value)
        o_path = None if (path is None) else path if isinstance(path, PathExpression) else str(path)
        o_neg = True if (negated is None) else not negated  # True means it is a positive constraint
        o_query = None if (query is None) else str(query)

        if path is not None and not isinstance(path, PathExpression):  # if the predicate is a url, add '<>' to it
            o_path = self.sparql_term(path)
        if is_inverse_path:
            o_path = "^" + o_path

        if shape_ref is not None:  # if the shape reference is a url, add '<>' to it
            o_shape_ref = self.sparql_term(shape_ref)

        if value is not None:  # if the value reference is a url, add '<>' to it
            o_value = self.sparql_term(value)

        if datatype is not None:  # if the data type is a url, add '<>' to it
            o_datatype = self.sparql_term(datatype)

        constraints = []

        if and_ is not None:
            shape_refs = [self.sparql_term(item["shape"]) for item in and_ if item.get("shape") is not None]
            if len(shape_refs) != len(and_):
                raise NotImplementedError("sh:and currently supports only shape references")
            constraints.append(AndConstraint(id_, shape_refs, o_neg, options, target_def))

        if xone is not None:
            if not xone:
                raise ValueError("sh:xone must contain at least one shape reference")
            shape_refs = [self.sparql_term(item["shape"]) for item in xone if isinstance(item, dict) and item.get("shape") is not None]
            if len(shape_refs) != len(xone):
                raise NotImplementedError("sh:xone currently supports only shape references")
            constraints.append(XoneConstraint(id_, shape_refs, o_neg, options, target_def))

        if isinstance(negated, dict):
            nested = self.parse_constraint(var_generator, negated, id_ + "_not", target_def, None)
            constraints.append(NotConstraint(var_generator, id_, nested, True, options, target_def))

        if closed:
            constraints.append(
                ClosedConstraint(
                    var_generator,
                    id_,
                    [PathExpression.from_string(path).to_sparql() for path in obj.get("allowedPaths", [])],
                    [self.sparql_term(path) for path in obj.get("ignoredProperties", [])],
                    o_neg,
                    options,
                    target_def,
                )
            )

        if o_path is None and constraints:
            return self.apply_constraint_metadata(constraints, obj)

        if o_path is not None:
            if qualified_shape is not None:
                q_shape_ref = qualified_shape.get("shape") if isinstance(qualified_shape, dict) else qualified_shape
                if q_shape_ref is None:
                    raise NotImplementedError("sh:qualifiedValueShape currently supports only sh:node references")
                if qualified_min is not None:
                    constraints.append(
                        QualifiedValueShapeConstraint(
                            var_generator,
                            id_,
                            o_path,
                            self.sparql_term(q_shape_ref),
                            qualified_min,
                            None,
                            o_neg,
                            options,
                            target_def,
                        )
                    )
                if qualified_max is not None:
                    constraints.append(
                        QualifiedValueShapeConstraint(
                            var_generator,
                            id_,
                            o_path,
                            self.sparql_term(q_shape_ref),
                            None,
                            qualified_max,
                            o_neg,
                            options,
                            target_def,
                        )
                    )
            if o_min is not None:
                if o_max is not None:
                    constraints.extend(
                        [
                            MinOnlyConstraint(
                                var_generator,
                                id_,
                                o_path,
                                o_min,
                                o_neg,
                                options,
                                o_datatype,
                                o_value,
                                o_shape_ref,
                                target_def,
                            ),
                            MaxOnlyConstraint(
                                var_generator,
                                id_,
                                o_path,
                                o_max,
                                o_neg,
                                options,
                                o_datatype,
                                o_value,
                                o_shape_ref,
                                target_def,
                            ),
                        ]
                    )
                else:
                    constraints.append(
                        MinOnlyConstraint(
                            var_generator,
                            id_,
                            o_path,
                            o_min,
                            o_neg,
                            options,
                            o_datatype,
                            o_value,
                            o_shape_ref,
                            target_def,
                        )
                    )
            if o_max is not None:
                constraints.append(
                    MaxOnlyConstraint(
                        var_generator,
                        id_,
                        o_path,
                        o_max,
                        o_neg,
                        options,
                        o_datatype,
                        o_value,
                        o_shape_ref,
                        target_def,
                    )
                )

            if obj.get("class") is not None:
                constraints.append(
                    ClassConstraint(
                        var_generator, id_, o_path, self.sparql_term(obj.get("class")), o_neg, options, target_def
                    )
                )
            if obj.get("nodeKind") is not None:
                constraints.append(
                    NodeKindConstraint(
                        var_generator, id_, o_path, self.sparql_term(obj.get("nodeKind")), o_neg, options, target_def
                    )
                )
            if obj.get("minInclusive") is not None:
                constraints.append(
                    RangeMinInclusiveConstraint(
                        var_generator, id_, o_path, obj.get("minInclusive"), o_neg, options, target_def
                    )
                )
            if obj.get("minExclusive") is not None:
                constraints.append(
                    RangeMinExclusiveConstraint(
                        var_generator, id_, o_path, obj.get("minExclusive"), o_neg, options, target_def
                    )
                )
            if obj.get("maxInclusive") is not None:
                constraints.append(
                    RangeMaxInclusiveConstraint(
                        var_generator, id_, o_path, obj.get("maxInclusive"), o_neg, options, target_def
                    )
                )
            if obj.get("maxExclusive") is not None:
                constraints.append(
                    RangeMaxExclusiveConstraint(
                        var_generator, id_, o_path, obj.get("maxExclusive"), o_neg, options, target_def
                    )
                )
            if obj.get("minLength") is not None:
                constraints.append(
                    MinLengthConstraint(var_generator, id_, o_path, obj.get("minLength"), o_neg, options, target_def)
                )
            if obj.get("maxLength") is not None:
                constraints.append(
                    MaxLengthConstraint(var_generator, id_, o_path, obj.get("maxLength"), o_neg, options, target_def)
                )
            if obj.get("pattern") is not None:
                constraints.append(
                    PatternConstraint(
                        var_generator, id_, o_path, obj.get("pattern"), o_neg, options, obj.get("flags"), target_def
                    )
                )
            if obj.get("languageIn") is not None:
                constraints.append(
                    LanguageInConstraint(var_generator, id_, o_path, obj.get("languageIn"), o_neg, options, target_def)
                )
            if self.parse_bool(obj.get("uniqueLang", False)):
                constraints.append(UniqueLangConstraint(var_generator, id_, o_path, o_neg, options, target_def))
            if has_value is not None:
                constraints.append(HasValueConstraint(var_generator, id_, o_path, self.sparql_term(has_value), o_neg, options, target_def))
            if in_values is not None:
                constraints.append(InConstraint(var_generator, id_, o_path, in_values, o_neg, options, target_def))
            if obj.get("equals") is not None:
                constraints.append(
                    PairEqualsConstraint(
                        var_generator, id_, o_path, self.sparql_term(obj.get("equals")), o_neg, options, target_def
                    )
                )
            if obj.get("disjoint") is not None:
                constraints.append(
                    PairDisjointConstraint(
                        var_generator, id_, o_path, self.sparql_term(obj.get("disjoint")), o_neg, options, target_def
                    )
                )
            if obj.get("lessThan") is not None:
                constraints.append(
                    PairLessThanConstraint(
                        var_generator, id_, o_path, self.sparql_term(obj.get("lessThan")), o_neg, options, target_def
                    )
                )
            if obj.get("lessThanOrEquals") is not None:
                constraints.append(
                    PairLessThanOrEqualsConstraint(
                        var_generator,
                        id_,
                        o_path,
                        self.sparql_term(obj.get("lessThanOrEquals")),
                        o_neg,
                        options,
                        target_def,
                    )
                )

            if constraints:
                return self.apply_constraint_metadata(constraints, obj)
        elif o_query is not None:
            return self.apply_constraint_metadata([SPARQLConstraint(id_, o_neg, o_query)], obj)
        elif options is not None:
            return self.apply_constraint_metadata(
                [
                    MinOnlyConstraint(
                        var_generator, id_, o_path, o_min, o_neg, options, o_datatype, o_value, o_shape_ref, target_def
                    )
                ],
                obj,
            )

        if self.ignore_errors:
            log.warning("There was an unsupported constraint, skipping it...")
        else:
            raise NotImplementedError("It seems you are using an unsupported feature. Please, check your shape schema.")
        log.warning("There was an unsupported constraint, skipping it...")
        return []
