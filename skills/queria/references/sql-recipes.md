# Queria SQL Recipes

Run with `uvx queria sql "<query>"`.
Reference tables as `dataset.schema.table`. Referencing another dataset attaches it
automatically, so you can join across datasets directly. Prefer `mart_`-prefixed tables
for analysis-ready data.

Data values (place names, item names, categories) are in Japanese — filter and search
with Japanese strings as shown below.

## Discovery and schema inspection

```bash
uvx queria list                     # list datasets
uvx queria search 不動産             # search datasets/tables/columns ("real estate")
uvx queria info reinfolib           # metadata (license, source, schema)
uvx queria schema e_stat            # list tables
uvx queria columns reinfolib        # columns (types, descriptions)
uvx queria summarize zipcode.main.mart_zipcode   # column stats (full scan)
```

Inspect columns of any table directly:
```sql
SELECT column_name, column_type FROM (DESCRIBE e_stat.ssds.a_pref_population)
```

## Postal codes x municipality codes

```sql
SELECT g.prefecture, g.city, COUNT(*) AS zip_count
FROM zipcode.main.mart_zipcode z
JOIN lg_code.main.mart_lg_code g ON z.lg_code = g.lg_code
GROUP BY 1, 2 ORDER BY zip_count DESC
```

## Corporations: gBizINFO x NTA corporate numbers (join on corporate_number)

Top companies by capital stock:
```sql
SELECT h.name, h.prefecture_name, c.capital_stock, c.employee_number
FROM gbizinfo.main.mart_gbizinfo_company c
JOIN houjin_bangou.main.mart_houjin_bangou h
  ON c.corporate_number = h.corporate_number
WHERE c.capital_stock IS NOT NULL
ORDER BY c.capital_stock DESC LIMIT 20
```

Subsidy recipients (enrich location from houjin_bangou):
```sql
SELECT h.prefecture_name, COUNT(*) AS subsidies
FROM gbizinfo.main.mart_gbizinfo_subsidy s
JOIN houjin_bangou.main.mart_houjin_bangou h
  ON s.corporate_number = h.corporate_number
GROUP BY 1 ORDER BY subsidies DESC
```

## Statistics: e-Stat SSDS (System of Social and Demographic Statistics)

SSDS tables are long-format (`item_name`, `area_name`, `year`, `value`). Filter
indicators by `item_name`. The same (area, year) may contain multiple `cat01` values
or time points, so also filter by `cat01` when needed.

Find available indicator names (総人口 = total population):
```sql
SELECT DISTINCT item_name FROM e_stat.ssds.a_pref_population WHERE item_name LIKE '%総人口%'
```

Total population by prefecture (latest year, excluding 全国 = nationwide):
```sql
SELECT area_name, value
FROM e_stat.ssds.a_pref_population
WHERE item_name = 'A1101_総人口'
  AND year = (SELECT MAX(year) FROM e_stat.ssds.a_pref_population
              WHERE item_name = 'A1101_総人口')
  AND area_name <> '全国'
QUALIFY ROW_NUMBER() OVER (PARTITION BY area_name ORDER BY value DESC) = 1
ORDER BY value DESC
```

Search across statistical tables (what tables exist; 人口 = population):
```sql
SELECT statistics_name, table_title, collect_area
FROM e_stat.main.stats_catalog
WHERE lower(statistics_name || ' ' || table_title) LIKE '%人口%' LIMIT 20
```

## Statistics x municipality codes (municipality-level joins)

SSDS `_municipal_` tables have `area` (5-digit municipality code), which joins to
`lg_code_5` in lg_code. The latest year differs per indicator, so scope the year
subquery to the same `item_name`:
```sql
SELECT g.prefecture, g.city, p.value AS population
FROM e_stat.ssds.a_municipal_population p
JOIN lg_code.main.mart_lg_code g ON p.area = g.lg_code_5
WHERE p.item_name = 'A1101_総人口'
  AND p.year = (SELECT MAX(year) FROM e_stat.ssds.a_municipal_population
                WHERE item_name = 'A1101_総人口')
QUALIFY ROW_NUMBER() OVER (PARTITION BY p.area ORDER BY p.value DESC) = 1  -- dedupe breakdown rows
ORDER BY population DESC LIMIT 20
```
(Match code digit counts on both sides with `columns` before joining. e_stat `area` is
5 digits; lg_code has the 6-digit `lg_code` and the 5-digit `lg_code_5`.)

## Geography: national land numerical information (GIS)

Boundary polygons have a `geometry` column. The spatial extension is preloaded, so
`ST_*` functions work:
```sql
SELECT prefecture_name, ST_Area(geometry) AS area
FROM nlftp.boundary.prefecture
ORDER BY area DESC LIMIT 10
```
(Coordinates are lat/lon, so areas are in degrees — suitable for relative comparison
and maps. Check column names with `uvx queria columns nlftp`.)

## Real estate

```sql
SELECT prefecture, COUNT(*) AS deals, AVG(trade_price) AS avg_price
FROM reinfolib.main.mart_trade_prices
GROUP BY 1 ORDER BY deals DESC
```
(Check actual columns with `uvx queria columns reinfolib`.)

## Handing off to other skills (visualization / analysis / dashboards)

This skill does not visualize. Write results out and pass them along:
```bash
uvx queria sql "
  SELECT area_name, value FROM e_stat.ssds.a_pref_population
  WHERE item_name='A1101_総人口' AND year=2024 AND area_name<>'全国'
" --out /tmp/pref_population.parquet
```
Pass the written CSV/Parquet to data:create-viz (charts) / data:analyze (analysis) /
data:build-dashboard or Tableau/PowerBI MCP (dashboards).
