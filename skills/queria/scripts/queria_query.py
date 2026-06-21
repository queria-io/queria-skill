#!/usr/bin/env python3
"""Queria open-data explorer.

Connect to Queria's public DuckLake catalogs (data.queria.io) read-only and
explore open data: list datasets, inspect schemas, search, and run SQL.

This script is self-contained. Running it with a plain `python3` is enough:
on first use it creates a private virtualenv (default: ~/.cache/queria/venv),
installs `duckdb` there, and re-executes itself with that interpreter. Nothing
is installed into your global environment, and `uv` is not required.

Scope: connection + exploration + retrieval only. Visualization, dashboards,
and analysis are intentionally out of scope -- export results with --out and
hand them to other skills (data:create-viz, data:analyze, BI MCPs, ...).

Note on versions: Queria publishes DuckLake v1 catalogs. The duckdb pin below
is coupled to that format -- bump it if Queria's catalog format changes.
"""

from __future__ import annotations

import os
import re
import sys

# duckdb version requirement, coupled to Queria's published DuckLake v1 format.
# The catalog is DuckLake format 1.0; only duckdb >= 1.5.4 ships a ducklake
# extension new enough to read it (1.5.1's is too old). Bump both if Queria's
# catalog format changes.
DUCKDB_SPEC = "duckdb>=1.5.4"
MIN_DUCKDB = (1, 5, 4)
_BOOTSTRAP_FLAG = "QUERIA_QUERY_BOOTSTRAPPED"


def _duckdb_ok() -> bool:
    """True if an importable duckdb meets the minimum version for DuckLake 1.0."""
    try:
        import duckdb
    except ImportError:
        return False
    parts = []
    for chunk in duckdb.__version__.split(".")[:3]:
        m = re.match(r"\d+", chunk)
        parts.append(int(m.group()) if m else 0)
    return tuple(parts) >= MIN_DUCKDB


def _lib_dir() -> str:
    """Private install dir for duckdb, keyed by python + duckdb version.

    Keying by version means a bumped pin installs into a fresh directory rather
    than clashing with an older cached copy. Wheels are python-version specific,
    so the interpreter version is part of the key too.
    """
    cache = os.environ.get("XDG_CACHE_HOME") or os.path.join(
        os.path.expanduser("~"), ".cache"
    )
    ver = "".join(str(n) for n in MIN_DUCKDB)
    key = f"pylib-py{sys.version_info.major}{sys.version_info.minor}-duckdb{ver}"
    return os.path.join(cache, "queria", key)


def _ensure_duckdb() -> None:
    """Ensure a duckdb new enough for DuckLake 1.0 is importable.

    A globally-installed duckdb is used only when it meets MIN_DUCKDB. Otherwise
    the pinned version is installed into a private directory via ``pip install
    --target`` (no venv/ensurepip, no global pollution) and the script re-execs
    itself with that directory on PYTHONPATH.
    """
    if _duckdb_ok():
        return

    # Guard against an infinite re-exec loop.
    if os.environ.get(_BOOTSTRAP_FLAG) == "1":
        sys.exit(
            "duckdb is unavailable or too old even after setup.\n"
            f"Try removing {_lib_dir()} and re-running, or install manually:\n"
            f"  python3 -m pip install '{DUCKDB_SPEC}'"
        )

    import subprocess

    target = _lib_dir()
    if not os.path.isdir(os.path.join(target, "duckdb")):
        print(
            f"[queria] First run: installing duckdb into {target}\n"
            "[queria] (one-time; your global Python is left untouched)",
            file=sys.stderr,
        )
        try:
            subprocess.run(
                [
                    sys.executable, "-m", "pip", "install", "--quiet",
                    "--target", target, DUCKDB_SPEC,
                ],
                check=True,
            )
        except (subprocess.CalledProcessError, OSError) as e:
            sys.exit(
                "[queria] Failed to install duckdb.\n"
                f"  reason: {e}\n"
                "  Check your network connection and that python3 has pip,\n"
                f"  or install manually: python3 -m pip install '{DUCKDB_SPEC}'"
            )

    # Re-exec with the private dir first on PYTHONPATH so it shadows any older
    # global duckdb.
    env = dict(os.environ, **{_BOOTSTRAP_FLAG: "1"})
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = target + (os.pathsep + existing if existing else "")
    os.execve(
        sys.executable,
        [sys.executable, os.path.abspath(__file__), *sys.argv[1:]],
        env,
    )


_ensure_duckdb()

# ---- below this line, duckdb is guaranteed importable -----------------------

import argparse  # noqa: E402
import re  # noqa: E402

import duckdb  # noqa: E402

DEFAULT_STORAGE = "https://data.queria.io"
CATALOG_ALIAS = "catalog"
MAX_AUTO_ATTACH = 8

# Only these statement kinds are allowed for user-supplied --sql. Everything is
# read-only; writes to the catalog are rejected.
_READONLY_RE = re.compile(
    r"^\s*(with|select|describe|show|pragma|explain|summarize|values|table|from)\b",
    re.IGNORECASE,
)
_MISSING_CATALOG_RE = re.compile(r'Catalog "?([A-Za-z0-9_]+)"? does not exist')


def _attach_sql(storage: str, alias: str) -> str:
    url = f"{storage}/{alias}/ducklake.duckdb"
    data_path = f"{storage}/{alias}/ducklake.duckdb.files/"
    return (
        f"ATTACH 'ducklake:{url}' AS {alias} "
        f"(READ_ONLY, DATA_PATH '{data_path}', OVERRIDE_DATA_PATH true)"
    )


def _connect(storage: str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL ducklake; LOAD ducklake;")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    # spatial: several datasets (nlftp, address_br, e_stat boundaries) expose
    # GEOMETRY columns and ST_* functions.
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(_attach_sql(storage, CATALOG_ALIAS))
    return con


def _run(
    con: duckdb.DuckDBPyConnection, sql: str, storage: str
) -> duckdb.DuckDBPyRelation:
    """Execute a query, auto-attaching datasets referenced but not yet attached."""
    attached = {CATALOG_ALIAS}
    for _ in range(MAX_AUTO_ATTACH + 1):
        try:
            return con.sql(sql)
        except duckdb.Error as e:
            # A reference to a not-yet-attached dataset surfaces as a missing
            # catalog (Catalog/Binder exception). Attach it and retry.
            m = _MISSING_CATALOG_RE.search(str(e))
            if not m or m.group(1) in attached:
                raise
            alias = m.group(1)
            con.execute(_attach_sql(storage, alias))
            attached.add(alias)
    return con.sql(sql)


def _print_table(rel: duckdb.DuckDBPyRelation) -> None:
    cols = rel.columns
    rows = [[("" if v is None else str(v)) for v in row] for row in rel.fetchall()]
    widths = [len(c) for c in cols]
    for row in rows:
        for i, v in enumerate(row):
            widths[i] = max(widths[i], len(v))
    print(" | ".join(c.ljust(w) for c, w in zip(cols, widths)))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(" | ".join(v.ljust(w) for v, w in zip(row, widths)))
    print(f"\n({len(rows)} rows)", file=sys.stderr)


def _emit(con, sql: str, storage: str, fmt: str, out: str | None) -> None:
    if out:
        ext = os.path.splitext(out)[1].lower()
        copy_fmt = "PARQUET" if ext == ".parquet" else "CSV, HEADER"
        # Ensure referenced datasets are attached before COPY.
        _run(con, sql, storage)
        con.execute(f"COPY ({sql}) TO '{out}' (FORMAT {copy_fmt})")
        print(f"Wrote {out}", file=sys.stderr)
        return
    rel = _run(con, sql, storage)
    if fmt == "table":
        _print_table(rel)
    elif fmt == "csv":
        con.execute(f"COPY ({sql}) TO '/dev/stdout' (FORMAT CSV, HEADER)")
    elif fmt == "json":
        con.execute(f"COPY ({sql}) TO '/dev/stdout' (FORMAT JSON)")


def cmd_list(con, args) -> None:
    sql = (
        "SELECT datasource, title, description "
        f"FROM {CATALOG_ALIAS}.main.mart_datasets ORDER BY datasource"
    )
    _emit(con, sql, args.storage, args.format, args.out)


def cmd_schema(con, args) -> None:
    ds = args.schema
    sql = f"""
        SELECT n.schema_name, n.name AS table_name, n.description
        FROM {CATALOG_ALIAS}.main.mart_nodes n
        WHERE n.datasource = '{ds}' AND n.resource_type = 'model'
        ORDER BY n.schema_name, n.name
    """
    _emit(con, sql, args.storage, args.format, args.out)


def cmd_columns(con, args) -> None:
    ds = args.columns
    sql = f"""
        SELECT table_name, column_name, data_type, description
        FROM {CATALOG_ALIAS}.main.mart_columns
        WHERE datasource = '{ds}'
        ORDER BY table_name, column_name
    """
    _emit(con, sql, args.storage, args.format, args.out)


def cmd_search(con, args) -> None:
    kw = args.search.replace("'", "''")
    sql = f"""
        SELECT datasource, title, description
        FROM {CATALOG_ALIAS}.main.mart_datasets
        WHERE lower(title || ' ' || COALESCE(description, '')) LIKE lower('%{kw}%')
        ORDER BY datasource
    """
    _emit(con, sql, args.storage, args.format, args.out)


def cmd_sql(con, args) -> None:
    if not _READONLY_RE.match(args.sql):
        sys.exit(
            "Only read-only queries are allowed "
            "(SELECT/WITH/DESCRIBE/SHOW/PRAGMA/EXPLAIN/SUMMARIZE)."
        )
    _emit(con, args.sql, args.storage, args.format, args.out)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Explore Queria public open data (read-only).",
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="list available datasets")
    g.add_argument("--search", metavar="KEYWORD", help="search datasets by keyword")
    g.add_argument("--schema", metavar="DATASET", help="list a dataset's tables")
    g.add_argument(
        "--columns", metavar="DATASET", help="list a dataset's columns"
    )
    g.add_argument("--sql", metavar="QUERY", help="run a read-only SQL query")
    p.add_argument(
        "--datasets",
        help="comma-separated datasets to pre-attach (usually auto-detected)",
    )
    p.add_argument(
        "--format", choices=["table", "csv", "json"], default="table",
        help="stdout format (ignored when --out is set)",
    )
    p.add_argument("--out", help="write result to a .csv or .parquet file")
    p.add_argument(
        "--storage-url", dest="storage", default=DEFAULT_STORAGE,
        help=f"catalog base URL (default: {DEFAULT_STORAGE})",
    )
    args = p.parse_args()

    con = _connect(args.storage)
    try:
        if args.datasets:
            for ds in (d.strip() for d in args.datasets.split(",") if d.strip()):
                con.execute(_attach_sql(args.storage, ds))
        if args.list:
            cmd_list(con, args)
        elif args.search:
            cmd_search(con, args)
        elif args.schema:
            cmd_schema(con, args)
        elif args.columns:
            cmd_columns(con, args)
        elif args.sql:
            cmd_sql(con, args)
    finally:
        con.close()


if __name__ == "__main__":
    main()
