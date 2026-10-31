# Cold Chain — T-Val Compliance App

A Databricks App, packaged as a Databricks Asset Bundle, for tracking fleet temperature-validation (T-Val) compliance. Operations staff enter and update compliance records in a spreadsheet-style grid, and every save is written to a governed Delta table in Unity Catalog. It replaces a shared tracking spreadsheet.

The bundle includes two versions of the app. Both use the same tables and the same save logic, and you can deploy either one or both:

| App | Resource key | Stack | Source |
|---|---|---|---|
| v1 | `cold_chain` | Dash + AG Grid (pure Python) | `src/app/` |
| v2 (APX) | `cold_chain_apx` | FastAPI + React/TypeScript/Vite/Tailwind | `src/apx_app/` (backend + built SPA), `frontend/` (React source) |

## What it does

- Editable spreadsheet-style grid over a Delta table.
- **Unit #** is a dropdown fed from a trailer master table, so only valid units can be entered.
- **T-Val Status** is a dropdown with a filter (for example, show only compliant units).
- **Last Updated** and **Updated By** are stamped on save from the signed-in user's identity.
- Add and delete rows. **Save** writes everything back to Delta in one atomic `INSERT OVERWRITE`.
- Summary cards show total, compliant, and non-compliant units.

The data lives in Unity Catalog, ready to join with shipment data or use in dashboards.

## Repo layout

```
databricks.yml                     # bundle, variables, dev/prod targets
resources/cold_chain.app.yml       # v1 Dash app + SQL warehouse resource + env config
resources/cold_chain_apx.app.yml   # v2 FastAPI + React app (same config)
resources/setup_tables.job.yml     # one-off job that creates and seeds the tables
setup/create_tables.sql            # DDL + synthetic sample data (idempotent)
src/app/                           # v1: Dash UI (app.py) + Delta data layer (backend.py)
src/apx_app/                       # v2: FastAPI API (app.py) + same data layer + compiled SPA in static/
frontend/                          # v2: React source; `npm run build` writes to src/apx_app/static
```

## Prerequisites

- A Unity Catalog catalog where you can create a schema (or an existing schema you can write to)
- A SQL warehouse (serverless recommended)
- Databricks CLI v0.250+

## Deploy

```bash
git clone https://github.com/susan-farjami-db/cold-chain-compliance-app.git
cd cold-chain-compliance-app

VARS='--var=warehouse_id=<warehouse-id> --var=catalog=<catalog>'

databricks bundle validate $VARS --profile <profile>
databricks bundle deploy   $VARS --profile <profile>

# 1. Create the schema + tables and seed sample data (safe to re-run)
databricks bundle run setup_tables $VARS --profile <profile>

# 2. Start the app(s)
databricks bundle run cold_chain     $VARS --profile <profile>   # v1 (Dash)
databricks bundle run cold_chain_apx $VARS --profile <profile>   # v2 (FastAPI + React)
```

`bundle deploy` creates both apps. To deploy only one, delete the other's file from `resources/`.

Then give each app's service principal access to the data. Find the ID with `databricks apps get cold-chain-dev` (or `cold-chain-apx-dev`), field `service_principal_client_id`:

```sql
GRANT USE CATALOG ON CATALOG <catalog> TO `<service-principal-id>`;
GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA <catalog>.cold_chain TO `<service-principal-id>`;
```

To deploy the shared production copy, add `-t prod`. The apps are then named `cold-chain-prod` and `cold-chain-apx-prod`.

## Rebuilding the v2 frontend

The compiled SPA in `src/apx_app/static/` is committed, so deploying doesn't need Node. Rebuild only if you change `frontend/src`:

```bash
cd frontend
npm install
npm run build        # writes to ../src/apx_app/static
```

For local development, run the API with `python src/apx_app/app.py` (port 8080, with the same env vars as in `resources/cold_chain_apx.app.yml`) and `npm run dev` in `frontend/`. Vite proxies `/api` to the API.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `warehouse_id` | (required) | SQL warehouse for app reads/writes and the setup job |
| `catalog` | (required) | Catalog for the tables |
| `schema` | `cold_chain` | Schema for the tables |
| `trailer_table` | `<catalog>.<schema>.trailers` | Fully qualified table feeding the Unit # dropdown. Point it at your real fleet master |
| `trailer_id_col` | `trailer_id` | ID column in `trailer_table` |

If you point `trailer_table` at your own fleet master, grant the app's service principal `SELECT` on that table too.

## Data model

`cold_chain_compliance` columns:

| Field | Column |
|---|---|
| Unit Number | `unit_number` (dropdown) |
| Trailer | `trailer_type` |
| Contractor vs Owner | `owner_name` |
| Last Update Date | `last_update_date` (auto) |
| Detailed description | `last_change_description` |
| User who updated | `updated_by` (auto) |
| Pending action items | `pending_action_items` |
| Compliant for T-Val | `tval_status` (dropdown + filter) |
| Re-Cert / Install Appt | `recert_appt_date` |

All sample data from `setup/create_tables.sql` is synthetic.

## Notes

- Saves replace the whole table with the grid's contents in a single transaction. That's fine for a small HQ-maintained list, but the last writer wins if two people edit at the same time.
- The app reads and writes data as its service principal. The signed-in user's email is used only to fill in **Updated By**.
