"""Run Trav-SHACL over SPP turtle inputs.

Usage:
    .venv/bin/python run_spp_validation.py [SHAPES_TTL] [DATA_TTL]

Defaults:
    SHAPES_TTL = software-project-plan.v5.0.0.ttl (also used as DATA_TTL if no
                 second arg, i.e. the schema itself is the graph being checked)
    DATA_TTL   = same as SHAPES_TTL

When DATA_TTL differs from SHAPES_TTL, the two graphs are merged into one
in-memory rdflib Graph and passed to Trav-SHACL as both ``schema_dir`` and
``endpoint`` (Trav-SHACL accepts a Graph for either side). Output goes to
``output/<run-tag>/``, where run-tag is the data-file stem.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from rdflib import Graph

from TravSHACL import parse_heuristics
from TravSHACL.core.GraphTraversal import GraphTraversal
from TravSHACL.core.ShapeSchema import ShapeSchema
from TravSHACL.sparql import SPARQLEndpoint as _SE


_orig_run = _SE.SPARQLEndpoint._SPARQLEndpoint__SPARQLEndpoint.run_query  # type: ignore[attr-defined]
_QUERY_LOG: list[str] = []
_FAIL_DUMP: Path | None = None


def _traced_run(self, query_string):
    _QUERY_LOG.append(query_string)
    try:
        return _orig_run(self, query_string)
    except Exception:
        if _FAIL_DUMP is not None:
            _FAIL_DUMP.parent.mkdir(parents=True, exist_ok=True)
            with _FAIL_DUMP.open("w") as f:
                for q in _QUERY_LOG[-3:]:
                    f.write("# ---- query ----\n")
                    f.write(q)
                    f.write("\n\n")
        raise


_SE.SPARQLEndpoint._SPARQLEndpoint__SPARQLEndpoint.run_query = _traced_run  # type: ignore[attr-defined]

ROOT = Path(__file__).parent
DEFAULT_SHAPES = ROOT / "example" / "spp" / "software-project-plan.v5.0.0.ttl"


def _load(path: Path) -> Graph:
    g = Graph()
    g.parse(str(path), format="turtle")
    return g


def _value_to_str(v):
    # rdflib node → display string for JSON
    try:
        return v.n3() if hasattr(v, "n3") else str(v)
    except Exception:
        return str(v)


def run(shapes_path: Path, data_path: Path, out_dir: Path) -> dict:
    global _FAIL_DUMP
    out_dir.mkdir(parents=True, exist_ok=True)
    _FAIL_DUMP = out_dir / "failed-queries.sparql"

    print(f"[load] shapes: {shapes_path.name}", flush=True)
    t0 = time.time()
    shapes_g = _load(shapes_path)
    print(f"[load]   {len(shapes_g)} triples in {time.time()-t0:.2f}s", flush=True)

    if data_path == shapes_path:
        data_g = shapes_g
        merged = shapes_g
        print("[load] data: (same file as shapes)", flush=True)
    else:
        print(f"[load] data: {data_path.name}", flush=True)
        t0 = time.time()
        data_g = _load(data_path)
        print(f"[load]   {len(data_g)} triples in {time.time()-t0:.2f}s", flush=True)
        # Trav-SHACL expects shapes graph for the parser and a data endpoint for
        # SPARQL. We merge into a single graph because the schema also defines
        # supporting ontology terms (rdfs:subClassOf chains used by sh:class).
        merged = Graph()
        for t in shapes_g:
            merged.add(t)
        for t in data_g:
            merged.add(t)
        print(f"[load] merged graph: {len(merged)} triples", flush=True)

    print("[build] constructing ShapeSchema ...", flush=True)
    schema = ShapeSchema(
        schema_dir=shapes_g,
        endpoint=merged,
        graph_traversal=GraphTraversal.DFS,
        heuristics=parse_heuristics("TARGET IN BIG"),
        use_selective_queries=False,
        max_split_size=256,
        output_dir=str(out_dir),
        order_by_in_queries=False,
        save_outputs=True,
        ignore_parsing_errors=True,
    )
    print(f"[build] parsed {len(schema.shapes)} shapes", flush=True)

    print("[validate] running interleaved validation + Turtle report ...", flush=True)
    t0 = time.time()
    per_shape, turtle_report = schema.validate(report_format="turtle")
    elapsed = time.time() - t0
    print(f"[validate] done in {elapsed:.2f}s", flush=True)

    totals = {"valid": 0, "invalid": 0}
    per_shape_summary = {}
    for shape_id, buckets in per_shape.items():
        v = list(buckets.get("valid_instances", []) or [])
        i = list(buckets.get("invalid_instances", []) or [])
        totals["valid"] += len(v)
        totals["invalid"] += len(i)
        if v or i:
            per_shape_summary[shape_id] = {
                "valid": len(v),
                "invalid": len(i),
                "invalid_examples": [_value_to_str(x) for x in i[:5]],
            }

    census_q = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?cls (COUNT(?s) AS ?n) WHERE { ?s rdf:type ?cls }
        GROUP BY ?cls ORDER BY DESC(?n)
    """
    census = [(str(r.cls), int(r.n)) for r in data_g.query(census_q)]

    summary = {
        "shapes_input": shapes_path.name,
        "data_input": data_path.name,
        "triples_shapes": len(shapes_g),
        "triples_data": len(data_g),
        "triples_merged": len(merged),
        "shapes_parsed": len(schema.shapes),
        "elapsed_seconds": round(elapsed, 3),
        "totals": totals,
        "per_shape_with_findings": per_shape_summary,
        "data_class_instance_census": [{"class": c, "count": n} for c, n in census],
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    (out_dir / "validation-report.ttl").write_text(turtle_report)
    (out_dir / "per-shape-raw.json").write_text(
        json.dumps(per_shape, indent=2, default=list, sort_keys=True)
    )

    print(f"[write] {out_dir}/summary.json", flush=True)
    print(f"[write] {out_dir}/validation-report.ttl ({len(turtle_report)} bytes)", flush=True)
    print(f"[write] {out_dir}/per-shape-raw.json", flush=True)
    print(
        f"[summary] shapes_with_findings={len(per_shape_summary)}  "
        f"valid={totals['valid']}  invalid={totals['invalid']}",
        flush=True,
    )
    return summary


def main() -> int:
    args = sys.argv[1:]
    if not args:
        shapes = DEFAULT_SHAPES
        data = DEFAULT_SHAPES
    elif len(args) == 1:
        shapes = DEFAULT_SHAPES
        data = Path(args[0]).resolve()
    else:
        shapes = Path(args[0]).resolve()
        data = Path(args[1]).resolve()

    tag = data.stem
    out_dir = ROOT / "output" / tag
    run(shapes, data, out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
