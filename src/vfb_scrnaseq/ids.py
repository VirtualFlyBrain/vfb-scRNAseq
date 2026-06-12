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
from dataclasses import dataclass
from pathlib import Path

PREFIX = "VFBseq"
ID_WIDTH = 8  # VFBseq_00000001

#: Entity types we mint ids for. Mirrors the LinkML classes.
ENTITY_TYPES = ("Dataset", "Sample", "Assay", "Clustering", "Cluster")


def _format_id(counter: int) -> str:
    return f"{PREFIX}_{counter:0{ID_WIDTH}d}"


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

    @classmethod
    def load(cls, path: str | Path) -> "IDRegistry":
        path = Path(path)
        if path.exists():
            data = json.loads(path.read_text())
            reg = cls(path=path, _counter=data["counter"], _entries=data["entries"])
        else:
            reg = cls(path=path, _counter=0, _entries={})
        return reg

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
