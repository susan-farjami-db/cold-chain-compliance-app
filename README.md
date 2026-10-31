# Cold Chain — T-Val Compliance App

A Databricks App (Dash + AG Grid), packaged as a Databricks Asset Bundle, for tracking fleet temperature-validation (T-Val) compliance. Operations staff enter and update compliance records in a spreadsheet-style grid, and every save is written to a governed Delta table in Unity Catalog. It replaces a shared tracking spreadsheet.

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
resources/cold_chain.app.yml       # Databricks App + SQL warehouse resource + env config
resources/setup_tables.job.yml     # one-off job that creates and seeds the tables
setup/create_tables.sql            # DDL + synthetic sample data (idempotent)
src/app/app.py                     # Dash UI
src/app/backend.py                 # Delta read/write through the SQL warehouse
src/app/requirements.txt
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

# 2. Start the app
databricks bundle run cold_chain $VARS --profile <profile>
```

Then give the app's service principal access to the data. Find its ID with `databricks apps get cold-chain-dev` (field `service_principal_client_id`):

```sql
GRANT USE CATALOG ON CATALOG <catalog> TO `<service-principal-id>`;
GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA <catalog>.cold_chain TO `<service-principal-id>`;
```

To deploy the shared production copy, add `-t prod`. The app is then named `cold-chain-prod`.

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
