"""
fault_checker.py — Pre-task anticipatory fault lookup. Gevurah function.

Before starting any operation, call check() with the layer_type you're about
to work on. If previous blocks of that type recorded faults, you get them
back as context: "last time I did this type of thing, this went wrong."

This is Changeling's first primitive of anticipatory learning — not pattern
matching over statistics, but concrete memory of specific past failures. The
chain doesn't let you forget what went wrong. You have to reason about it
before proceeding.
"""

import sqlite3
from typing import Optional

from changeling.chain_reader import by_fault, by_type


def check(
    conn: sqlite3.Connection,
    layer_type: str,
    fault_substring: Optional[str] = None,
) -> list[dict]:
    """
    Return all past fault blocks for a given layer_type.

    Call this before starting a task of type layer_type. If the returned list
    is non-empty, the system has faulted on this type of operation before.
    The caller should read the fault and reasoning fields before proceeding.

    Args:
      layer_type:      The type of operation about to be performed.
      fault_substring: Optional — further filter to faults containing this
                       string (useful for checking specific known failure modes).

    Returns:
      List of fault blocks for the given type, oldest first.
      Empty list = no prior faults for this type.
    """
    fault_blocks = by_fault(conn, fault_substring)
    return [b for b in fault_blocks if b["layer_type"] == layer_type]


def has_faults(
    conn: sqlite3.Connection,
    layer_type: str,
    fault_substring: Optional[str] = None,
) -> bool:
    """Convenience wrapper — True if any prior faults exist for this type."""
    return len(check(conn, layer_type, fault_substring)) > 0


def summarise_faults(
    conn: sqlite3.Connection,
    layer_type: str,
) -> Optional[str]:
    """
    Return a plain-text summary of all known faults for a layer_type.
    Returns None if no faults exist. Useful for including in reasoning fields.
    """
    faults = check(conn, layer_type)
    if not faults:
        return None

    lines = [f"Known faults for layer_type={layer_type!r}:"]
    for f in faults:
        lines.append(
            f"  [{f['timestamp']}] fault={f['fault']!r}  reasoning={f['reasoning']!r}"
        )
    return "\n".join(lines)
