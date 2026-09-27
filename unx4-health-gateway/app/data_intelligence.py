import json
from typing import Any

from .change_engine import diff_records


def canonical_map(records: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(record[key]): record for record in records if record.get(key) is not None}


def persist_changes(conn, dataset: str, before: dict[str, dict[str, Any]],
                     after: dict[str, dict[str, Any]], sync_run_id: int) -> list[dict[str, Any]]:
    changes = diff_records(before, after)
    for change in changes:
        conn.execute(
            """INSERT INTO data_changes(
                dataset, entity_id, change_type, changed_fields, before, after, sync_run_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (
                dataset,
                change.get("entity_id"),
                change["change_type"],
                json.dumps(change.get("changed_fields", [])),
                json.dumps(change.get("before"), default=str) if change.get("before") is not None else None,
                json.dumps(change.get("after"), default=str) if change.get("after") is not None else None,
                sync_run_id,
            ),
        )
    return changes


def apply_soft_removals(conn, table: str, id_column: str,
                        before_ids: set[str], after_ids: set[str]) -> list[str]:
    removed = sorted(before_ids - after_ids)
    if removed:
        placeholders = ",".join(["%s"] * len(removed))
        conn.execute(
            f"UPDATE {table} SET active=FALSE WHERE {id_column} IN ({placeholders})",
            removed,
        )
    return removed


def activate_current(conn, table: str, id_column: str, ids: set[str]) -> None:
    if not ids:
        return
    placeholders = ",".join(["%s"] * len(ids))
    conn.execute(
        f"UPDATE {table} SET active=TRUE WHERE {id_column} IN ({placeholders})",
        list(ids),
    )
