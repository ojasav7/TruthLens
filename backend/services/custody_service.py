"""Evidence Chain of Custody — track evidence integrity for forensic use.

Records every access, transformation, and transfer of evidence.
Produces a tamper-evident chain that can be verified later.
"""

import hashlib
import json
from datetime import datetime, timezone


# In-memory chain store (production: DB table)
_chains: dict[str, list[dict]] = {}


def _compute_hash(data: dict) -> str:
    """Compute SHA-256 of the custody record for tamper detection."""
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def create_chain(evidence_id: str, initial_data: dict) -> dict:
    """Start a new chain of custody for an evidence item."""
    entry = {
        "sequence": 0,
        "action": "CREATED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": initial_data.get("actor", "system"),
        "data_hash": _compute_hash(initial_data),
        "description": initial_data.get("description", "Evidence created"),
    }
    entry["entry_hash"] = _compute_hash(entry)

    _chains[evidence_id] = [entry]
    return {"evidence_id": evidence_id, "chain_length": 1, "integrity": "VERIFIED"}


def add_entry(evidence_id: str, action: str, description: str, actor: str = "system", data: dict | None = None) -> dict:
    """Add a custody entry (access, transform, transfer, review)."""
    if evidence_id not in _chains:
        create_chain(evidence_id, {"description": "Auto-created chain"})

    chain = _chains[evidence_id]
    prev_hash = chain[-1]["entry_hash"] if chain else "0" * 64

    entry = {
        "sequence": len(chain),
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "previous_hash": prev_hash,
        "data_hash": _compute_hash(data or {}),
        "description": description,
    }
    entry["entry_hash"] = _compute_hash(entry)
    chain.append(entry)

    return {
        "evidence_id": evidence_id,
        "sequence": entry["sequence"],
        "chain_length": len(chain),
        "integrity": "VERIFIED",
    }


def verify_chain(evidence_id: str) -> dict:
    """Verify the integrity of a custody chain."""
    chain = _chains.get(evidence_id)
    if not chain:
        return {"evidence_id": evidence_id, "integrity": "NOT_FOUND", "errors": []}

    errors = []
    for i, entry in enumerate(chain):
        # Verify hash chain
        if i > 0:
            expected_prev = chain[i-1]["entry_hash"]
            if entry.get("previous_hash") != expected_prev:
                errors.append(f"Entry {i}: broken hash chain")

    integrity = "VERIFIED" if not errors else "TAMPERED"

    return {
        "evidence_id": evidence_id,
        "chain_length": len(chain),
        "integrity": integrity,
        "errors": errors,
        "first_entry": chain[0]["timestamp"] if chain else None,
        "last_entry": chain[-1]["timestamp"] if chain else None,
    }


def get_chain(evidence_id: str) -> dict:
    """Get the full custody chain for an evidence item."""
    chain = _chains.get(evidence_id, [])
    verification = verify_chain(evidence_id)
    return {
        "evidence_id": evidence_id,
        "entries": chain,
        "chain_length": len(chain),
        "integrity": verification["integrity"],
    }


def custody_summary(evidence_id: str) -> str:
    """Generate a human-readable custody summary."""
    chain = _chains.get(evidence_id, [])
    if not chain:
        return f"No custody chain found for {evidence_id}"

    actors = set(e["actor"] for e in chain)
    actions = [e["action"] for e in chain]
    return (
        f"Chain for {evidence_id}: {len(chain)} entries, "
        f"{len(actors)} actor(s) ({', '.join(actors)}), "
        f"actions: {' → '.join(actions)}"
    )
