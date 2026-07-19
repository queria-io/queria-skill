---
name: queria
description: Explore and query Queria's public Japanese open data (data.queria.io) with read-only SQL. Covers postal codes (郵便番号), corporate numbers (法人番号), e-Stat government statistics (政府統計), national land numerical information (国土数値情報), real estate, calendars, municipality codes, and more, with cross-dataset joins. Use when asked to find or use data via Queria, explore Japanese open data (日本のオープンデータ), or join datasets across sources. Hands off visualization, analysis, and dashboards to other skills.
---

# Queria Open Data Exploration

Queria publishes Japanese open data as DuckLake catalogs (data.queria.io).
This skill connects to those catalogs read-only to discover datasets, inspect schemas,
retrieve data with SQL, and join across datasets. Visualization, statistical analysis,
and dashboards are out of scope — write results out with `--out` and hand them to other
skills (data:create-viz, data:analyze, data:build-dashboard, Tableau/PowerBI MCP, etc.).

No authentication or local build is required; everything runs read-only and is safe to
execute (anonymous access is rate-limited; if you hit the limit, set up a token following
https://docs.queria.io/connection/authentication).
There is no static list of datasets — always discover them from the catalog with `list` / `search`.

Most data values (place names, statistics categories, company names) are in Japanese.
Search with Japanese keywords when possible; table and column names are in English.

## How to run

Use the queria CLI (PyPI: `queria`). With uv, no install is needed:

```bash
uvx queria list
```

Without uv, `pip install queria` and run `queria list`.
If the uvx cache is stale, run `uvx queria@latest list` to get the latest version.

### Commands

| Command | Purpose |
|---|---|
| `uvx queria list` | List datasets |
| `uvx queria search <keyword>` | Search across datasets, tables, and columns (start discovery here). `--type dataset\|table\|column` `--limit N` |
| `uvx queria info <dataset>` | Metadata (license, source URL, schema, last updated). `--readme` includes the README body |
| `uvx queria schema <dataset>` | List tables with descriptions |
| `uvx queria columns <dataset> [table]` | Columns (with types and descriptions) |
| `uvx queria summarize <dataset>.<schema>.<table>` | Column statistics (row count, min/max, NULL rate). Full scan — beware of large tables |
| `uvx queria sql "<query>"` | Run read-only SQL |
| `--out <file.csv\|.parquet>` | Write results to a file (for handing off to other skills) |
| `--format table\|csv\|json\|jsonl\|markdown` | Stdout format (default: table; ignored when `--out` is given) |

## Exploration workflow

1. Discover: `uvx queria search 人口` ("population" — use Japanese keywords; run `uvx queria list` if unsure what exists)
2. Check provenance: `uvx queria info e_stat` — license and source URL are shown here
3. Understand the schema: `uvx queria schema e_stat` → `uvx queria columns e_stat <table>`
4. Peek at the data: `uvx queria sql "SELECT ... LIMIT 20"` (use `summarize` to see distributions)
5. Retrieve: `uvx queria sql "<query>"`
6. Hand off: if visualization or analysis is needed, write out with `--out result.parquet` and pass it to another skill

### Writing SQL

Reference tables as `dataset.schema.table` (e.g. `zipcode.main.mart_zipcode`).
Each dataset is a separate catalog, but referencing multiple datasets attaches them
automatically so you can join across them.
Analysis-ready tables use the `mart_` prefix (`raw_` is raw data, `stg_` is intermediate).

Cross-dataset join example (postal codes x municipality codes):

```sql
SELECT g.prefecture, g.city, COUNT(*) AS zip_count
FROM zipcode.main.mart_zipcode z
JOIN lg_code.main.mart_lg_code g ON z.lg_code = g.lg_code
GROUP BY 1, 2 ORDER BY zip_count DESC
```

### Common join keys

Keys frequently used for joins across datasets (always verify actual digit counts and
column names with `columns`):

- `lg_code`: national local government code (全国地方公共団体コード, identifies
  prefectures and municipalities). `lg_code.main.mart_lg_code` is the join hub, holding
  the 6-digit `lg_code` and the 5-digit `lg_code_5`. The 5-digit `area` column in e-Stat
  municipality-level tables joins to `lg_code_5`
- `corporate_number`: corporate number (法人番号). Joins corporate datasets to each other
- `key_code`: joins boundary polygons (e.g. census small areas) to statistics

See `references/sql-recipes.md` for common queries.

## Visualization / analysis / dashboards (out of scope)

This skill does not do these. After retrieving data, hand off by purpose:

- Charts and graphs: write results with `--out result.csv` and pass to data:create-viz / data:data-visualization
- Statistical analysis and reports: pass to data:analyze / data:statistical-analysis
- Dashboards: pass to data:build-dashboard, or Tableau/PowerBI MCP

## Constraints

- Public data (data.queria.io) only, read-only. The CLI rejects write SQL.
- `summarize` and unfiltered SELECTs scan all remote data.
  Probe with `LIMIT` first.
- Never ATTACH DuckLake directly from the DuckDB CLI (version mismatch corrupts the
  catalog). Always go through the queria CLI. If the catalog format has been updated,
  the CLI error message explains the required upgrade.
