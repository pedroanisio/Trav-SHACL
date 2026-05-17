import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path):
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _read_cases():
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((REPO_ROOT / "tests/cases").rglob("*"))
        if path.is_file() and path.suffix in {".json", ".ttl"}
    )


def _section(text, title, next_title=None):
    start = text.index(title)
    if next_title is None:
        return text[start:]
    end = text.index(next_title, start)
    return text[start:end]


def _shape_schema_example_kwargs(text):
    kwargs = []
    in_call = False
    for line in text.splitlines():
        if "ShapeSchema(" in line:
            in_call = True
            continue
        if in_call and re.match(r"\s*\)", line):
            in_call = False
            continue
        if in_call:
            match = re.match(r"\s+([A-Za-z_][A-Za-z0-9_]*)=", line)
            if match:
                kwargs.append(match.group(1))
    return kwargs


def _compose_service_block(compose_text, service_name):
    pattern = rf"^  {re.escape(service_name)}:\n(?P<block>.*?)(?=^  [A-Za-z0-9_-]+:\n|^networks:|\Z)"
    match = re.search(pattern, compose_text, flags=re.MULTILINE | re.DOTALL)
    assert match, f"Missing compose service: {service_name}"
    return match.group("block")


def _compose_scalar(service_block, key):
    match = re.search(rf"^\s+{re.escape(key)}:\s*(?P<value>.+)$", service_block, flags=re.MULTILINE)
    assert match, f"Missing compose key: {key}"
    return match.group("value").strip().strip("'\"")


def _compose_list(service_block, key):
    match = re.search(
        rf"^\s+{re.escape(key)}:\n(?P<items>(?:\s+-\s+.+\n)+)",
        service_block,
        flags=re.MULTILINE,
    )
    assert match, f"Missing compose list: {key}"
    return [line.split("-", 1)[1].strip().strip("'\"") for line in match.group("items").splitlines()]


def _compose_port_mapping(service_block):
    mappings = _compose_list(service_block, "ports")
    assert len(mappings) == 1
    external_port, internal_port = mappings[0].split(":")
    return external_port, internal_port


def _dockerfile_env(name):
    match = re.search(rf"^ENV {re.escape(name)}=(?P<value>\S+)$", _read("Dockerfile"), flags=re.MULTILINE)
    assert match, f"Missing Dockerfile ENV {name}"
    return match.group("value")


def _shape_schema_constructor_signature():
    source = ast.parse(_read("TravSHACL/core/ShapeSchema.py"))
    for node in ast.walk(source):
        if isinstance(node, ast.ClassDef) and node.name == "ShapeSchema":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    names = [argument.arg for argument in item.args.kwonlyargs]
                    required = {
                        argument.arg
                        for argument, default in zip(item.args.kwonlyargs, item.args.kw_defaults, strict=False)
                        if default is None
                    }
                    return names, required
    raise AssertionError("ShapeSchema.__init__ not found")


def _flask_routes():
    source = ast.parse(_read("TravSHACL/app/__init__.py"))
    routes = set()
    for node in ast.walk(source):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "route"
                and isinstance(func.value, ast.Name)
                and func.value.id == "app"
                and decorator.args
                and isinstance(decorator.args[0], ast.Constant)
            ):
                routes.add(decorator.args[0].value)
    return routes


def _setup_kwargs():
    source = ast.parse(_read("setup.py"))
    for node in ast.walk(source):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "setup":
            return {
                keyword.arg: ast.literal_eval(keyword.value)
                for keyword in node.keywords
                if keyword.arg in {"classifiers", "python_requires"}
            }
    raise AssertionError("setup(...) call not found")


def _ci_python_versions():
    workflow = _read(".github/workflows/test.yml")
    match = re.search(r"python-version:\s*(\[[^\]]+\])", workflow)
    assert match, "Missing GitHub Actions Python matrix"
    return ast.literal_eval(match.group(1))


def _python_constant(path, name):
    source = ast.parse(_read(path))
    for node in source.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing Python constant: {name}")


def _isinstance_type_names(path):
    source = ast.parse(_read(path))
    names = set()
    for node in ast.walk(source):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "isinstance"
            and len(node.args) >= 2
        ):
            continue
        type_arg = node.args[1]
        if isinstance(type_arg, ast.Name):
            names.add(type_arg.id)
        elif isinstance(type_arg, ast.Tuple):
            names.update(item.id for item in type_arg.elts if isinstance(item, ast.Name))
    return names


def test_shape_schema_documented_parameters_match_constructor():
    library_doc = _read("docs/library.rst")
    parameters_section = _section(library_doc, "Parameters\n==========", "Results: Internal Structure")
    documented_parameters = re.findall(r"^\* ``([A-Za-z_][A-Za-z0-9_]*)``", parameters_section, flags=re.MULTILINE)

    constructor_parameters, required_parameters = _shape_schema_constructor_signature()

    assert documented_parameters == constructor_parameters

    required_sentence = re.search(r"only required parameters are ``([^`]+)`` and ``([^`]+)``", library_doc)
    assert required_sentence
    assert set(required_sentence.groups()) == required_parameters

    unknown_example_kwargs = set(_shape_schema_example_kwargs(library_doc)) - set(constructor_parameters)
    assert unknown_example_kwargs == set()


def test_service_docs_match_flask_docker_and_compose_contract():
    compose_text = _read("example/docker-compose.yml")
    service_doc = _read("docs/service.rst")

    engine_block = _compose_service_block(compose_text, "example_engine")
    data_block = _compose_service_block(compose_text, "example_data")
    engine_external_port, engine_internal_port = _compose_port_mapping(engine_block)
    data_external_port, data_internal_port = _compose_port_mapping(data_block)

    assert "/validate" in _flask_routes()
    assert engine_internal_port == _dockerfile_env("FLASK_RUN_PORT")

    engine_container = _compose_scalar(engine_block, "container_name")
    data_container = _compose_scalar(data_block, "container_name")
    engine_volume = _compose_list(engine_block, "volumes")[0]
    _, engine_shape_mount = engine_volume.split(":")

    assert f"``{data_container}``" in service_doc
    assert f"``{engine_container}``" in service_doc
    assert f"http://localhost:{data_external_port}/sparql" in service_doc
    assert f"http://localhost:{engine_external_port}/validate" in service_doc
    assert f"http://{data_container}:{data_internal_port}/sparql" in service_doc
    assert f"``{engine_shape_mount}/LUBM``" in service_doc


def test_supported_python_versions_match_ci_matrix():
    setup_kwargs = _setup_kwargs()
    classifiers = setup_kwargs["classifiers"]
    classifier_versions = sorted(
        (
            classifier.rsplit("::", 1)[1].strip()
            for classifier in classifiers
            if re.match(r"Programming Language :: Python :: 3\.\d+$", classifier)
        ),
        key=lambda version: tuple(int(part) for part in version.split(".")),
    )
    ci_versions = _ci_python_versions()

    assert classifier_versions == ci_versions
    assert setup_kwargs["python_requires"] == f">={ci_versions[0]}"


def test_test_endpoint_contract_matches_compose_and_ci():
    compose_text = _read("tests/docker-compose.yml")
    workflow = _read(".github/workflows/test.yml")
    test_data_block = _compose_service_block(compose_text, "test_data")
    external_port, _ = _compose_port_mapping(test_data_block)
    endpoint_url = f"http://localhost:{external_port}/sparql"

    assert _python_constant("tests/test_cases.py", "TEST_ENDPOINT") == endpoint_url
    assert "cd tests" in workflow
    assert "docker compose up -d" in workflow
    assert f"--fail {endpoint_url}" in workflow


def test_constraint_dispatch_stays_polymorphic():
    checked_paths = [
        "TravSHACL/sparql/QueryGenerator.py",
        "TravSHACL/core/Shape.py",
        "TravSHACL/rule_based_validation/Validation.py",
        "TravSHACL/rule_based_validation/InstancesRetrieval.py",
    ]
    allowed = set()
    offenders = {
        name
        for path in checked_paths
        for name in _isinstance_type_names(path)
        if name.endswith("Constraint") and name not in allowed
    }

    assert offenders == set()


def test_feature_claims_have_source_or_fixture_evidence():
    feature_doc = _read("docs/feature.rst")
    case_text = _read_cases()
    parser_source = _read("TravSHACL/core/ShapeParser.py")
    constraint_source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((REPO_ROOT / "TravSHACL/constraints").glob("*.py"))
    )
    endpoint_source = _read("TravSHACL/sparql/SPARQLEndpoint.py")
    test_cases_source = _read("tests/test_cases.py")

    supported_claims = {
        "cardinality": (
            ["``sh:minCount``", "``sh:maxCount``"],
            ["sh:minCount", "sh:maxCount"],
        ),
        "datatype": (
            ["``sh:datatype``"],
            ['NAMESPACE_SHACL + "datatype"', "self.datatype = datatype"],
        ),
        "relaxed shape-based constraints": (
            ["``sh:qualifiedValueShape``", "``sh:qualifiedMinCount``", "``sh:qualifiedMaxCount``"],
            ["sh:qualifiedValueShape", "sh:qualifiedMinCount", "sh:qualifiedMaxCount", "QualifiedValueShapeConstraint"],
        ),
        "direct value constraints": (
            ["``sh:hasValue``", "``sh:in``"],
            ["sh:hasValue", "sh:in", "HasValueConstraint", "InConstraint"],
        ),
        "closed shapes": (
            ["``sh:closed``", "``sh:ignoredProperties``"],
            ["sh:closed", "ignoredProperties", "ClosedConstraint"],
        ),
        "SPARQL constraints": (
            ["``sh:sparql``", "``sh:select``"],
            ["sh:sparql", "sh:select", "SPARQLConstraint"],
        ),
        "logical or": (
            ["``sh:or``"],
            ["sh:or"],
        ),
        "inverse paths": (
            ["sh:inversePath"],
            ["sh:inversePath"],
        ),
        "extended paths": (
            ["``sh:alternativePath``", "``sh:zeroOrMorePath``", "``sh:oneOrMorePath``", "``sh:zeroOrOnePath``"],
            ["alternativePath", "zeroOrMorePath", "oneOrMorePath", "zeroOrOnePath"],
        ),
        "value-type constraints": (
            ["``sh:class``", "``sh:nodeKind``"],
            ["sh:class", "sh:nodeKind", "ClassConstraint", "NodeKindConstraint"],
        ),
        "value-range constraints": (
            ["``sh:minInclusive``", "``sh:maxExclusive``"],
            ["sh:minInclusive", "sh:maxExclusive", "RangeMinInclusiveConstraint", "RangeMaxExclusiveConstraint"],
        ),
        "string constraints": (
            ["``sh:minLength``", "``sh:pattern``", "``sh:languageIn``", "``sh:uniqueLang``"],
            [
                "sh:minLength",
                "sh:pattern",
                'NAMESPACE_SHACL + "languageIn"',
                'NAMESPACE_SHACL + "uniqueLang"',
                "PatternConstraint",
            ],
        ),
        "property-pair constraints": (
            ["``sh:equals``", "``sh:disjoint``", "``sh:lessThan``", "``sh:lessThanOrEquals``"],
            ["sh:equals", "sh:disjoint", "sh:lessThan", "sh:lessThanOrEquals", "PairLessThanConstraint"],
        ),
        "private SPARQL endpoints": (
            ["private SPARQL endpoints via HTTP Basic Auth"],
            ["setHTTPAuth(BASIC)", "setCredentials"],
        ),
        "RDFLib graphs": (
            ["RDFLib graphs"],
            ["TEST_GRAPH", "@pytest.mark.parametrize"],
        ),
    }

    evidence_text = "\n".join([case_text, parser_source, constraint_source, endpoint_source, test_cases_source])
    for claim_name, (doc_markers, evidence_markers) in supported_claims.items():
        missing_doc_markers = [marker for marker in doc_markers if marker not in feature_doc]
        missing_evidence_markers = [marker for marker in evidence_markers if marker not in evidence_text]

        assert missing_doc_markers == [], claim_name
        assert missing_evidence_markers == [], claim_name


def test_example_docs_match_compose_topology():
    compose_text = _read("example/docker-compose.yml")
    library_doc = _read("docs/library.rst")
    service_doc = _read("docs/service.rst")
    example_readme = _read("example/README.md")

    data_block = _compose_service_block(compose_text, "example_data")
    engine_block = _compose_service_block(compose_text, "example_engine")
    data_external_port, _ = _compose_port_mapping(data_block)
    engine_external_port, _ = _compose_port_mapping(engine_block)

    assert "docker-compose -f ./example/docker-compose.yml up -d example_data" in library_doc
    assert "docker-compose -f ./example/docker-compose.yml up -d" in service_doc
    assert "docker-compose up -d --build" in example_readme

    assert "example_data" in compose_text
    assert "example_engine" in compose_text
    assert f"http://localhost:{data_external_port}/sparql" in library_doc
    assert f"http://localhost:{data_external_port}/sparql" in service_doc
    assert f"http://localhost:{data_external_port}/sparql" in example_readme
    assert f"http://localhost:{engine_external_port}/validate" in service_doc


def test_every_constraint_has_source_component():
    """Every concrete Constraint subclass declares a SHACL §4 component IRI.

    Forcing function for the polymorphic-dispatch pattern: any new subclass
    must record its sh:sourceConstraintComponent IRI via the SOURCE_COMPONENT
    class attribute (or override get_source_component() for dual-mode cases
    like MinMaxConstraint and QualifiedValueShapeConstraint).

    The Constraint base intentionally has SOURCE_COMPONENT = None.
    """
    # Import every concrete subclass to ensure __subclasses__() sees them.
    import importlib
    import os
    constraints_dir = os.path.join(os.path.dirname(__file__), "..", "TravSHACL", "constraints")
    for entry in sorted(os.listdir(constraints_dir)):
        if entry.endswith(".py") and entry not in {"__init__.py", "Constraint.py"}:
            importlib.import_module("TravSHACL.constraints." + entry[:-3])

    from TravSHACL.constraints.Constraint import Constraint

    def all_subclasses(cls):
        seen = set()
        for sub in cls.__subclasses__():
            if sub not in seen:
                seen.add(sub)
                yield sub
                yield from all_subclasses(sub)

    missing = []
    for sub in all_subclasses(Constraint):
        # Use the class-attribute access to avoid instance state requirements.
        # get_source_component() needs an instance for dual-mode subclasses; the
        # class attribute is the static contract checked here.
        value = sub.SOURCE_COMPONENT
        if value is None or not isinstance(value, str) or not value.startswith("http://www.w3.org/ns/shacl#"):
            missing.append((sub.__name__, value))

    assert missing == [], f"Constraint subclasses missing SOURCE_COMPONENT: {missing}"
