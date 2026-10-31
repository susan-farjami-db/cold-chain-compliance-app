"""Cold Chain — T-Val compliance data-entry app.

Dash + AG Grid editable grid backed by a Delta table. HQ users add/update
fleet T-Val compliance records; Last Update Date and Updated By are stamped
automatically on save from the app login identity.
"""
import os
import re
import uuid
from datetime import date

import dash
from dash import Dash, html, dcc, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from flask import request
from databricks.sdk import WorkspaceClient

import backend

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    title="Cold Chain — T-Val Compliance",
    suppress_callback_exceptions=True,
)
server = app.server


_ws = None
_name_cache = {}


def _workspace_client():
    global _ws
    if _ws is None:
        _ws = WorkspaceClient()  # app service principal
    return _ws


def _name_from_email(email):
    """Fallback: turn 'jane.doe@example.com' into 'Jane Doe'."""
    local = email.split("@")[0]
    parts = [p for p in re.split(r"[._-]+", local) if p]
    return " ".join(w.capitalize() for w in parts) if parts else email


def _display_name_for(email):
    """Resolve a friendly display name for the signed-in user's email.

    Tries the Unity Catalog / SCIM user directory first (exact name), then
    falls back to a title-cased name derived from the email.
    """
    if not email or "@" not in email:
        return email or "unknown-user"
    if email in _name_cache:
        return _name_cache[email]
    name = None
    try:
        for u in _workspace_client().users.list(filter=f'userName eq "{email}"', count=1):
            if u.display_name:
                name = u.display_name
                break
    except Exception:
        name = None
    if not name:
        name = _name_from_email(email)
    _name_cache[email] = name
    return name


def _current_user():
    """Display name of the signed-in app user (from the forwarded credential)."""
    h = request.headers
    email = h.get("X-Forwarded-Email") or h.get("X-Forwarded-Preferred-Username") or ""
    return _display_name_for(email) if email else "unknown-user"


def _column_defs(unit_options):
    status_style = {
        "styleConditions": [
            {
                "condition": "params.value == 'Compliant for T-Val'",
                "style": {"backgroundColor": "#e6f4ea", "color": "#137333"},
            },
            {
                "condition": "params.value && params.value != 'Compliant for T-Val'",
                "style": {"backgroundColor": "#fce8e6", "color": "#c5221f"},
            },
        ]
    }
    readonly_style = {"backgroundColor": "#f4f4f5", "color": "#6b7280"}
    return [
        {
            "headerName": "Unit #",
            "field": "unit_number",
            "editable": True,
            "cellEditor": "agSelectCellEditor",
            "cellEditorParams": {"values": unit_options},
            "width": 110,
            "pinned": "left",
            "checkboxSelection": True,
            "headerCheckboxSelection": True,
        },
        {"headerName": "Trailer", "field": "trailer_type", "editable": True, "width": 160},
        {"headerName": "Owner / Contractor", "field": "owner_name", "editable": True, "width": 210},
        {
            "headerName": "T-Val Status",
            "field": "tval_status",
            "editable": True,
            "cellEditor": "agSelectCellEditor",
            "cellEditorParams": {"values": backend.TVAL_STATUSES},
            "width": 210,
            "cellStyle": status_style,
        },
        {
            "headerName": "Last Change Description",
            "field": "last_change_description",
            "editable": True,
            "width": 340,
            "wrapText": True,
            "autoHeight": True,
            "cellEditor": "agLargeTextCellEditor",
            "cellEditorPopup": True,
        },
        {
            "headerName": "Pending Action Items",
            "field": "pending_action_items",
            "editable": True,
            "width": 240,
            "wrapText": True,
            "autoHeight": True,
            "cellEditor": "agLargeTextCellEditor",
            "cellEditorPopup": True,
        },
        {
            "headerName": "Re-Cert / Install Appt",
            "field": "recert_appt_date",
            "editable": True,
            "width": 190,
        },
        {
            "headerName": "Last Updated (auto)",
            "field": "last_update_date",
            "editable": False,
            "width": 150,
            "cellStyle": readonly_style,
        },
        {
            "headerName": "Updated By (auto)",
            "field": "updated_by",
            "editable": False,
            "width": 170,
            "cellStyle": readonly_style,
        },
    ]


def _blank_row():
    # Everything blank; Unit # and T-Val Status are chosen from their dropdowns.
    # updated_by (from credentials) and last_update_date are stamped on Save.
    return {
        "row_id": str(uuid.uuid4()),
        "unit_number": "",
        "trailer_type": "",
        "owner_name": "",
        "tval_status": "",
        "last_change_description": "",
        "pending_action_items": "",
        "recert_appt_date": "",
        "last_update_date": "",
        "updated_by": "",
    }


app.layout = dbc.Container(
    [
        dcc.Store(id="snapshot"),   # original loaded rows, keyed by row_id
        dcc.Store(id="user-store"),
        html.Div(
            [
                html.H3(
                    [html.I(className="fa-solid fa-snowflake me-2", style={"color": "#0b6bcb"}), "Cold Chain — T-Val Compliance"],
                    className="mb-0 fw-bold",
                ),
                html.Small(
                    "Fleet temperature-validation compliance tracker",
                    className="text-muted",
                ),
            ],
            className="mt-3 mb-2",
        ),
        dbc.Row(id="summary-cards", className="g-2 mb-3"),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button([html.I(className="fa-solid fa-plus me-1"), "Add unit"], id="add-btn", color="secondary", outline=True, size="sm"),
                    width="auto",
                ),
                dbc.Col(
                    dbc.Button([html.I(className="fa-solid fa-trash me-1"), "Delete selected"], id="del-btn", color="secondary", outline=True, size="sm"),
                    width="auto",
                ),
                dbc.Col(),  # spacer
                dbc.Col(
                    dbc.Button([html.I(className="fa-solid fa-rotate me-1"), "Refresh"], id="refresh-btn", color="light", size="sm"),
                    width="auto",
                ),
                dbc.Col(
                    dbc.Button([html.I(className="fa-solid fa-floppy-disk me-1"), "Save changes"], id="save-btn", color="primary", size="sm"),
                    width="auto",
                ),
            ],
            className="g-2 align-items-center mb-2",
        ),
        html.Div(id="status-msg", className="mb-2"),
        dcc.Loading(
            id="grid-loading",
            type="circle",
            color="#0b6bcb",
            children=dag.AgGrid(
                id="grid",
                columnDefs=_column_defs([]),
                rowData=[],
                defaultColDef={
                    "resizable": True,
                    "sortable": True,
                    "filter": False,
                },
                dashGridOptions={
                    "rowSelection": "multiple",
                    "animateRows": True,
                    "singleClickEdit": True,
                    "stopEditingWhenCellsLoseFocus": True,
                },
                columnSize="responsiveSizeToFit",
                style={"height": "70vh"},
            ),
        ),
    ],
    fluid=True,
)


@app.callback(
    Output("grid", "rowData"),
    Output("grid", "columnDefs"),
    Output("snapshot", "data"),
    Output("user-store", "data"),
    Output("status-msg", "children"),
    Input("refresh-btn", "n_clicks"),
    Input("save-btn", "n_clicks"),
    State("grid", "rowData"),
    State("snapshot", "data"),
    prevent_initial_call=False,
)
def load_or_save(refresh_clicks, save_clicks, grid_rows, snapshot):
    triggered = ctx.triggered_id
    user = _current_user()

    def _reload(msg=None):
        rows = backend.load_compliance()
        for r in rows:
            r["row_id"] = str(uuid.uuid4())
        snap = {r["row_id"]: {f: r.get(f) for f in backend.EDITABLE_FIELDS} for r in rows}
        cols = _column_defs(backend.load_units())
        return rows, cols, snap, user, msg

    # SAVE
    if triggered == "save-btn" and save_clicks:
        try:
            snapshot = snapshot or {}
            today = date.today().isoformat()
            to_write = []
            changed = 0
            for r in (grid_rows or []):
                if not (r.get("unit_number") or "").strip():
                    continue
                rid = r.get("row_id")
                original = snapshot.get(rid)
                is_changed = original is None or any(
                    (r.get(f) or "") != (original.get(f) or "") for f in backend.EDITABLE_FIELDS
                )
                row = dict(r)
                if is_changed:
                    row["last_update_date"] = today
                    row["updated_by"] = user
                    changed += 1
                to_write.append(row)
            backend.save_compliance(to_write)
            rows, cols, snap, _, _ = _reload()
            msg = dbc.Alert(
                f"Saved. {changed} row(s) stamped with today's date and your username ({user}).",
                color="success", dismissable=True, className="py-2 mb-0",
            )
            return rows, cols, snap, user, msg
        except Exception as e:  # surface DB errors in the UI
            return no_update, no_update, no_update, user, dbc.Alert(
                f"Save failed: {e}", color="danger", dismissable=True, className="py-2 mb-0"
            )

    # INITIAL LOAD or REFRESH
    try:
        rows, cols, snap, u, _ = _reload()
        return rows, cols, snap, u, None
    except Exception as e:
        return [], _column_defs([]), {}, user, dbc.Alert(
            f"Could not load data: {e}", color="danger", className="py-2 mb-0"
        )


@app.callback(
    Output("grid", "rowData", allow_duplicate=True),
    Input("add-btn", "n_clicks"),
    State("grid", "rowData"),
    prevent_initial_call=True,
)
def add_row(n, rows):
    rows = list(rows or [])
    rows.insert(0, _blank_row())
    return rows


@app.callback(
    Output("grid", "rowData", allow_duplicate=True),
    Input("del-btn", "n_clicks"),
    State("grid", "selectedRows"),
    State("grid", "rowData"),
    prevent_initial_call=True,
)
def delete_rows(n, selected, rows):
    if not selected:
        return no_update
    sel_ids = {s.get("row_id") for s in selected}
    return [r for r in (rows or []) if r.get("row_id") not in sel_ids]


def _stat_card(value, label, color):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.Div(str(value), className="fs-3 fw-bold", style={"color": color}),
                    html.Div(label, className="text-muted small"),
                ]
            ),
            className="shadow-sm",
        ),
        width="auto",
    )


@app.callback(
    Output("summary-cards", "children"),
    Input("grid", "rowData"),
)
def update_summary(rows):
    rows = rows or []
    total = len([r for r in rows if (r.get("unit_number") or "").strip()])
    compliant = len([r for r in rows if r.get("tval_status") == "Compliant for T-Val"])
    pending = total - compliant
    return [
        _stat_card(total, "Units tracked", "#0b6bcb"),
        _stat_card(compliant, "Compliant for T-Val", "#137333"),
        _stat_card(pending, "Pending HQ approval", "#c5221f"),
    ]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("DATABRICKS_APP_PORT", "8080")), debug=False)
