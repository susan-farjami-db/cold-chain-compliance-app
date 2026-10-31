"""Data access layer for the Cold Chain T-Val compliance app (v2 / APX-style).

Reads/writes the Delta tables in <COLD_CHAIN_CATALOG>.<COLD_CHAIN_SCHEMA>
via a SQL warehouse, using the app service principal (SDK Config()).

This mirrors the proven v1 semantics exactly — same tables, same atomic
INSERT OVERWRITE save, same dropdown source. Only the presentation layer
(React + FastAPI) is new.
"""
import os
from databricks.sdk.core import Config
from databricks import sql

CATALOG = os.environ["COLD_CHAIN_CATALOG"]
SCHEMA = os.environ["COLD_CHAIN_SCHEMA"]
COMPLIANCE_TABLE = f"{CATALOG}.{SCHEMA}.cold_chain_compliance"

# Master trailer table that feeds the Unit Number dropdown (data integrity).
# Defaults to the sample `trailers` table; point TRAILER_TABLE / TRAILER_ID_COL
# at your real fleet master to repoint without code changes.
TRAILER_TABLE = os.getenv("TRAILER_TABLE") or f"{CATALOG}.{SCHEMA}.trailers"
TRAILER_ID_COL = os.getenv("TRAILER_ID_COL") or "trailer_id"

TVAL_STATUSES = [
    "Compliant for T-Val",
    "NOT ABLE TO HAUL TVAL UNTIL HQ APPROVES",
]

# Business fields the user can edit; used for change detection on save.
EDITABLE_FIELDS = [
    "unit_number",
    "trailer_type",
    "owner_name",
    "last_change_description",
    "pending_action_items",
    "tval_status",
    "recert_appt_date",
]

_cfg = Config()


def _connect():
    return sql.connect(
        server_hostname=_cfg.host,
        http_path=f"/sql/1.0/warehouses/{os.environ['DATABRICKS_WAREHOUSE_ID']}",
        credentials_provider=lambda: _cfg.authenticate,
    )


def load_compliance():
    """Return all compliance rows as a list of dicts (dates as strings)."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT unit_number, trailer_type, owner_name,
                   CAST(last_update_date AS STRING) AS last_update_date,
                   last_change_description, updated_by,
                   pending_action_items, tval_status, recert_appt_date
            FROM {COMPLIANCE_TABLE}
            ORDER BY unit_number
            """
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def load_units():
    """Return trailer/unit IDs for the Unit Number dropdown (from the trailer master)."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT DISTINCT {TRAILER_ID_COL} FROM {TRAILER_TABLE} "
            f"WHERE {TRAILER_ID_COL} IS NOT NULL ORDER BY {TRAILER_ID_COL}"
        )
        return [str(row[0]) for row in cur.fetchall()]


def save_compliance(rows):
    """Atomically replace the compliance table with the supplied rows.

    Uses a single INSERT OVERWRITE so the write is one transaction and is
    idempotent — repeated/overlapping saves cannot create duplicate rows.
    Each row is a dict with the 9 business/audit columns; `last_update_date`
    may be a 'YYYY-MM-DD' string or None. Blank Unit # rows are skipped.
    """
    valid = [r for r in rows if (r.get("unit_number") or "").strip()]
    with _connect() as conn, conn.cursor() as cur:
        if not valid:
            cur.execute(f"DELETE FROM {COMPLIANCE_TABLE}")
            return True
        row_ph = "(?, ?, ?, CAST(? AS DATE), ?, ?, ?, ?, ?)"
        placeholders = ", ".join([row_ph] * len(valid))
        params = []
        for r in valid:
            params.extend([
                (r.get("unit_number") or "").strip(),
                r.get("trailer_type"),
                r.get("owner_name"),
                r.get("last_update_date") or None,
                r.get("last_change_description"),
                r.get("updated_by"),
                r.get("pending_action_items"),
                r.get("tval_status"),
                r.get("recert_appt_date"),
            ])
        cur.execute(
            f"INSERT OVERWRITE {COMPLIANCE_TABLE} VALUES {placeholders}",
            params,
        )
    return True
