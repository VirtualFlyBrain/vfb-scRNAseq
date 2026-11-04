"""Stable, registry-backed minting of ``VFBseq`` entity identifiers.

Every published entity (Dataset, Sample, Assay, Clustering, Cluster) gets an
opaque, VFB-controlled IRI of the form ``VFBseq_00000001``. GEO/SRA accessions
are NOT used as identifiers; they are carried as cross-references on the entity
(see the schema's ``accession`` / ``site`` slots).

Minting is *idempotent*: calling :meth:`IDRegistry.mint` again with the same
``(entity_type, natural_key)`` returns the previously assigned id, so re-running
the pipeline does not churn identifiers. The registry is a plain JSON file under
version control so the id<->entity mapping is auditable.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

PREFIX = "VFBseq"
ID_WIDTH = 8  # VFBseq_00000001

#: Entity types we mint ids for. Mirrors the LinkML classes.
ENTITY_TYPES = ("Dataset", "Sample", "Assay", "Clustering", "Cluster")


def _format_id(counter: int) -> str:
    return f"{PREFIX}_{counter:0{ID_WIDTH}d}"


_COUNTER_RE = re.compile(r'"counter":\s*(\d+)')


def _git(cwd: Path, *args: str, stdin: str | None = None) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=cwd, input=stdin, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return r.stdout


def counters_elsewhere(path: Path) -> dict[str, int]:
    """{where: registry counter} for this registry on the repo's other branches and worktrees.

    Branches cut from the same main each mint from the same counter, so two open
    branches would issue the same ids. Looking at every local and remote-tracking
    branch (as of the last fetch) and every other worktree's working copy (ids
    minted there but not yet committed) lets a new mint start past all of them.
    Empty outside a git repository. Set VFBSEQ_IDS_LOCAL_ONLY=1 to skip.
    """
    if os.environ.get("VFBSEQ_IDS_LOCAL_ONLY"):
        return {}
    path = Path(path).resolve()
    top = _git(path.parent, "rev-parse", "--show-toplevel")
    if not top:
        return {}
    top = Path(top.strip()).resolve()
    rel = path.relative_to(top).as_posix()
    out: dict[str, int] = {}

    refs = (_git(top, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes") or "").split()
    refs = [r for r in refs if not r.endswith("/HEAD")]
    if refs:
        checked = _git(top, "cat-file", "--batch-check=%(objectname) %(objecttype)",
                       stdin="".join(f"{r}:{rel}\n" for r in refs)) or ""
        blobs: dict[str, list[str]] = {}
        for ref, line in zip(refs, checked.splitlines()):
            sha, _, kind = line.partition(" ")
            if kind == "blob":
                blobs.setdefault(sha, []).append(re.sub(r"^refs/(heads|remotes)/", "", ref))
        for sha, names in blobs.items():
            m = _COUNTER_RE.search((_git(top, "cat-file", "-p", sha) or "")[:500])
            if m:
                out[", ".join(names)] = int(m.group(1))

    for line in (_git(top, "worktree", "list", "--porcelain") or "").splitlines():
        if line.startswith("worktree "):
            wt = Path(line[len("worktree "):]).resolve()
            other = wt / rel
            if wt != top and other.exists():
                m = _COUNTER_RE.search(other.read_text()[:500])
                if m:
                    out[f"worktree {wt}"] = int(m.group(1))
    return out


@dataclass
class IDRegistry:
    """A JSON-backed, append-only registry of minted ``VFBseq`` ids.

    The natural key is what *uniquely identifies the real-world entity* within
    this project (e.g. a GEO sample accession ``GSM4731869`` for a Sample, or a
    cluster label for a Cluster). It is the dedupe key, never the id itself.
    """

    path: Path
    _counter: int = 0
    _entries: dict[str, dict] = None  # natural_key -> {id, entity_type, label, accession}
    _checked_elsewhere: bool = False   # other branches / worktrees looked at (once, before a new id)

    @classmethod
    def load(cls, path: str | Path) -> "IDRegistry":
        path = Path(path)
        if path.exists():
            data = json.loads(path.read_text())
            reg = cls(path=path, _counter=data["counter"], _entries=data["entries"])
            reg.check()
        else:
            reg = cls(path=path, _counter=0, _entries={})
        return reg

    def check(self) -> None:
        """Fail if two entries share an id, or the counter is behind an id in use.

        Both happen when branches that each minted ids are merged: git combines the
        entries and keeps one counter, so the same ids are issued twice.
        """
        seen: dict[str, str] = {}
        dups = []
        for key, entry in self._entries.items():
            if entry["id"] in seen:
                dups.append(f"{entry['id']}: {seen[entry['id']]} / {key}")
            seen[entry["id"]] = key
        if dups:
            raise ValueError(f"{self.path}: ids minted twice (re-mint one side):\n  " + "\n  ".join(dups))
        top = max((int(e["id"].rsplit("_", 1)[1]) for e in self._entries.values()), default=0)
        if top > self._counter:
            raise ValueError(f"{self.path}: counter {self._counter} is behind id {_format_id(top)}")

    def _key(self, entity_type: str, natural_key: str) -> str:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"unknown entity_type {entity_type!r}; expected one of {ENTITY_TYPES}")
        return f"{entity_type}::{natural_key}"

    def mint(
        self,
        entity_type: str,
        natural_key: str,
        *,
        label: str | None = None,
        accession: str | None = None,
    ) -> str:
        """Return the ``VFBseq`` id for an entity, minting a new one if needed.

        Idempotent on ``(entity_type, natural_key)``.
        """
        key = self._key(entity_type, natural_key)
        existing = self._entries.get(key)
        if existing is not None:
            return existing["id"]
        if not self._checked_elsewhere:
            self._skip_ids_claimed_elsewhere()
        self._counter += 1
        new_id = _format_id(self._counter)
        self._entries[key] = {
            "id": new_id,
            "entity_type": entity_type,
            "natural_key": natural_key,
            "label": label,
            "accession": accession,
        }
        return new_id

    def _skip_ids_claimed_elsewhere(self) -> None:
        """Before the first new id, move the counter past every other branch's / worktree's."""
        self._checked_elsewhere = True
        others = counters_elsewhere(self.path)
        if not others:
            return
        where, top = max(others.items(), key=lambda kv: kv[1])
        if top > self._counter:
            print(f"id registry: {where} has minted up to {_format_id(top)}; "
                  f"new ids start at {_format_id(top + 1)} (counter here was {self._counter})")
            self._counter = top

    def get(self, entity_type: str, natural_key: str) -> str | None:
        entry = self._entries.get(self._key(entity_type, natural_key))
        return entry["id"] if entry else None

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "prefix": PREFIX,
            "id_width": ID_WIDTH,
            "counter": self._counter,
            "entries": self._entries,
        }
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
