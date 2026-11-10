"""Validate and emit RDF using the standard LinkML tools.

Rather than hand-building triples, this drives the LinkML CLIs against a
``tree_root`` Container instance of the entities:
  - ``linkml-validate`` — checks the data conforms to the schema (types, ranges,
    required slots, and rejects unknown slots) → our validation pass;
  - ``linkml-convert -t ttl`` — emits RDF using the schema's slot_uri/class_uri
    (``emit_ttl``; the Container index node, a tree_root artefact, is stripped);
  - ``linkml-data2owl`` — OWL functional syntax from the schema's owl annotations
    (``emit_owl``), converted to RDF/XML with ROBOT (``to_owlxml``).

``emit_expression_owl`` renders the expression axioms directly from the schema's
gene template (too many for linkml-owl), then ROBOT-converts and gzips them.

Every function takes an optional ``schema_path``: the master schema (default), or an
*extension* schema in another repo (e.g. vfb-EPseq-ontology) that imports the master
one as ``vfb_scrnaseq`` and adds its own subclasses and tree_root container. See
:func:`load_schema`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from rdflib import Graph, RDF, URIRef


def _script(name: str) -> str:
    """Path to a console script for THIS interpreter (avoids a stray 3.9 shadow on PATH)."""
    p = os.path.join(sysconfig.get_path("scripts"), name)
    return p if os.path.exists(p) else name

SCHEMA_PATH = Path(__file__).parent / "schema" / "VFB_scRNAseq_schema.yaml"
#: Name an extension schema imports the master schema by (`imports: [vfb_scrnaseq]`).
SCHEMA_IMPORT_NAME = "vfb_scrnaseq"


@dataclass(frozen=True)
class Schema:
    """A schema as the LinkML CLIs need it.

    ``path`` is the file passed to the CLIs: the schema itself, or for an extension
    schema a merged copy (linkml-data2owl does not follow imports). ``container`` is
    the tree_root class declared in the schema's own file, and ``groups`` maps each
    entity type to its list slot on that container.
    """

    path: Path
    view: SchemaView
    container: str
    container_uri: URIRef
    groups: dict[str, str]


@lru_cache
def load_schema(schema_path: str | Path = SCHEMA_PATH) -> Schema:
    """Load the master schema or an extension of it (resolving `vfb_scrnaseq`)."""
    schema_path = Path(schema_path).resolve()
    importmap = {SCHEMA_IMPORT_NAME: str(SCHEMA_PATH.with_suffix(""))}
    view = SchemaView(str(schema_path), importmap=importmap)
    roots = [n for n, c in view.schema.classes.items() if c.tree_root]
    if len(roots) != 1:
        raise ValueError(f"{schema_path}: expected one tree_root class in the file, found {roots}")
    container = roots[0]
    groups = {s.range: s.name for s in view.class_induced_slots(container)}
    path = schema_path
    if schema_path != SCHEMA_PATH.resolve():
        view.merge_imports()
        path = Path(tempfile.mkdtemp()) / schema_path.name
        yaml_dumper.dump(view.schema, str(path))
        view = SchemaView(str(path))
    return Schema(path, view, container, URIRef(view.get_uri(container, expand=True)), groups)


def container_from_entities(entities: list[dict], schema_path: str | Path = SCHEMA_PATH) -> dict:
    """Group flat entity records into the tree_root Container shape."""
    groups = load_schema(schema_path).groups
    cont: dict[str, list] = {g: [] for g in groups.values()}
    for e in entities:
        if e["type"] not in groups:
            raise ValueError(f"entity type {e['type']!r} has no list on the schema's container")
        cont[groups[e["type"]]].append({k: v for k, v in e.items() if k != "type"})
    return {k: v for k, v in cont.items() if v}


def _dump(container: dict) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
        yaml.safe_dump(container, fh, sort_keys=False)
        return fh.name


def validate(container: dict, schema_path: str | Path = SCHEMA_PATH) -> None:
    """Run linkml-validate on the container; raise with the report on failure."""
    sch = load_schema(schema_path)
    r = subprocess.run([_script("linkml-validate"), "-s", str(sch.path), "-C", sch.container,
                        _dump(container)], capture_output=True, text=True)
    if r.returncode != 0 or "No issues found" not in r.stdout:
        raise RuntimeError(f"linkml-validate failed:\n{r.stdout}\n{r.stderr}")


def emit_ttl(entities: list[dict], out_path: str | Path,
             schema_path: str | Path = SCHEMA_PATH, do_validate: bool = True) -> Path:
    """Validate then convert entities to Turtle via the LinkML CLIs."""
    sch = load_schema(schema_path)
    container = container_from_entities(entities, schema_path)
    if do_validate:
        validate(container, schema_path)

    r = subprocess.run([_script("linkml-convert"), "-s", str(sch.path), "-C", sch.container,
                        "-t", "ttl", _dump(container)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"linkml-convert failed:\n{r.stderr}")

    g = Graph()
    g.parse(data=r.stdout, format="turtle")
    # strip the tree_root Container index node (not domain data)
    for cnode in list(g.subjects(RDF.type, sch.container_uri)):
        for triple in list(g.triples((cnode, None, None))):
            g.remove(triple)
    out_path = Path(out_path)
    g.serialize(destination=str(out_path), format="turtle")
    return out_path


def emit_owl(entities: list[dict], out_path: str | Path,
             schema_path: str | Path = SCHEMA_PATH, do_validate: bool = True) -> Path:
    """Emit OWL via linkml-owl, honouring the schema's owl.fstring/owl.template
    annotations (ClassAssertions, ObjectSomeValuesFrom restrictions, and the
    annotated expression axioms) — the VFB-pipeline-compatible representation.

    Output format follows the file extension (.ofn functional syntax, .owl RDF/XML,
    .ttl Turtle).
    """
    sch = load_schema(schema_path)
    container = container_from_entities(entities, schema_path)
    if do_validate:
        validate(container, schema_path)
    out_path = Path(out_path)
    r = subprocess.run(
        [_script("linkml-data2owl"), "-s", str(sch.path), "-C", sch.container, _dump(container),
         "-o", str(out_path)],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"linkml-data2owl failed:\n{r.stdout}\n{r.stderr}")
    return out_path


def _gene_template(sv: SchemaView) -> str:
    """The `gene` slot's owl.template string from the schema (the axiom shape spec)."""
    ann = sv.get_slot("gene").annotations
    a = ann.get("owl.template") if hasattr(ann, "get") else ann["owl.template"]
    return a.value


def emit_expression_owl(rows, out_owl_gz: str | Path, schema_path: str | Path = SCHEMA_PATH,
                        hide: str = "true") -> Path:
    """Emit the per-(cluster,gene) expression axioms as gzipped OWL/XML.

    Efficient: renders the schema's `gene` owl.template per row (Jinja, no per-row
    OWL parse), writes one .ofn, then a single `robot convert` -> .owl -> gzip.
    `rows` = iterable of (cluster_vfbseq_id, cluster_label, fbgn, symbol, level, extent).
    """
    import gzip as gz

    import jinja2

    sv = load_schema(schema_path).view
    tmpl = jinja2.Template(_gene_template(sv))
    header = "\n".join(f"Prefix({p}:=<{o.prefix_reference}>)" for p, o in sv.schema.prefixes.items())

    ofn = tempfile.NamedTemporaryFile("w", suffix=".ofn", delete=False)
    ofn.write(header + "\nOntology(\n")
    for cid, _label, fbgn, _sym, level, extent in rows:
        ofn.write(tmpl.render(id=f"vfb:{cid}", gene=f"FlyBase:{fbgn}",
                              expression_level=level, expression_extent=extent,
                              hide_in_terminfo=hide) + "\n")
    ofn.write(")\n")
    ofn.close()

    out_owl_gz = Path(out_owl_gz)
    robot = shutil.which("robot")
    if not robot:
        # fall back to gzipped functional syntax (no OWL/XML) with a warning
        alt = out_owl_gz.with_suffix("").with_suffix(".ofn.gz")
        with open(ofn.name, "rb") as fi, gz.open(alt, "wb") as fo:
            fo.writelines(fi)
        print(f"  robot not on PATH — wrote {alt} (functional syntax) instead of OWL/XML", file=sys.stderr)
        return alt
    with tempfile.NamedTemporaryFile(suffix=".owl", delete=False) as owl_tmp:
        owl_path = owl_tmp.name
    r = subprocess.run([robot, "convert", "-i", ofn.name, "-o", owl_path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"robot convert failed:\n{r.stdout}\n{r.stderr}")
    with open(owl_path, "rb") as fi, gz.open(out_owl_gz, "wb") as fo:
        fo.writelines(fi)
    return out_owl_gz


def to_owlxml(ofn_path: str | Path, out_path: str | Path | None = None) -> Path | None:
    """Convert an OWL functional-syntax (.ofn) file to OWL/XML (.owl) with ROBOT.

    ROBOT is an external Java tool (not a pip/uv dep); if it is not on PATH this
    is skipped with a warning and returns None rather than failing the pipeline.
    """
    robot = shutil.which("robot")
    ofn_path = Path(ofn_path)
    out_path = Path(out_path) if out_path else ofn_path.with_suffix(".owl")
    if not robot:
        print("  robot not on PATH — skipping OWL/XML (.owl) conversion", file=sys.stderr)
        return None
    r = subprocess.run([robot, "convert", "-i", str(ofn_path), "-o", str(out_path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"robot convert failed:\n{r.stdout}\n{r.stderr}")
    return out_path
