# Queria SQL レシピ集

`uvx queria sql "<query>"` で実行する。
テーブルは `データセット名.スキーマ.テーブル名` で参照。別データセットを参照すると自動アタッチされ、
そのまま横断結合できる。整形済みデータは `mart_` 接頭辞を優先する。

## 発見・スキーマ把握

```bash
uvx queria list                     # データセット一覧
uvx queria search 不動産             # データセット・テーブル・カラムの横断検索
uvx queria info reinfolib           # メタデータ（ライセンス・出典・スキーマ）
uvx queria schema e_stat            # テーブル一覧
uvx queria columns reinfolib        # カラム（型・説明）
uvx queria summarize zipcode.main.mart_zipcode   # カラム統計（全件スキャン）
```

任意テーブルのカラムを直接見る:
```sql
SELECT column_name, column_type FROM (DESCRIBE e_stat.ssds.a_pref_population)
```

## 郵便番号 × 自治体コード

```sql
SELECT g.prefecture, g.city, COUNT(*) AS zip_count
FROM zipcode.main.mart_zipcode z
JOIN lg_code.main.mart_lg_code g ON z.lg_code = g.lg_code
GROUP BY 1, 2 ORDER BY zip_count DESC
```

## 法人: gBizINFO × 国税庁法人番号（corporate_number で結合）

資本金トップ:
```sql
SELECT h.name, h.prefecture_name, c.capital_stock, c.employee_number
FROM gbizinfo.main.mart_gbizinfo_company c
JOIN houjin_bangou.main.mart_houjin_bangou h
  ON c.corporate_number = h.corporate_number
WHERE c.capital_stock IS NOT NULL
ORDER BY c.capital_stock DESC LIMIT 20
```

補助金の交付先（houjin_bangou で所在地を補完）:
```sql
SELECT h.prefecture_name, COUNT(*) AS subsidies
FROM gbizinfo.main.mart_gbizinfo_subsidy s
JOIN houjin_bangou.main.mart_houjin_bangou h
  ON s.corporate_number = h.corporate_number
GROUP BY 1 ORDER BY subsidies DESC
```

## 統計: e-Stat SSDS（社会・人口統計体系）

SSDS テーブルは long 形式（`item_name`, `area_name`, `year`, `value`）。指標は `item_name` で絞る。
同一 (area, year) に複数の `cat01` / 時点が含まれることがあるので、必要に応じ `cat01` でも絞る。

利用できる指標名を調べる:
```sql
SELECT DISTINCT item_name FROM e_stat.ssds.a_pref_population WHERE item_name LIKE '%総人口%'
```

都道府県別 総人口（最新年・全国除く）:
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

統計表を横断検索する（どの統計表があるか）:
```sql
SELECT statistics_name, table_title, collect_area
FROM e_stat.main.stats_catalog
WHERE lower(statistics_name || ' ' || table_title) LIKE '%人口%' LIMIT 20
```

## 統計 × 自治体コード（市区町村粒度の結合）

SSDS の `_municipal_` 系は `area`（5桁自治体コード）を持ち、lg_code の `lg_code_5` と結合できる。
最新年は指標ごとに異なるため、年のサブクエリは同じ `item_name` で絞ること:
```sql
SELECT g.prefecture, g.city, p.value AS population
FROM e_stat.ssds.a_municipal_population p
JOIN lg_code.main.mart_lg_code g ON p.area = g.lg_code_5
WHERE p.item_name = 'A1101_総人口'
  AND p.year = (SELECT MAX(year) FROM e_stat.ssds.a_municipal_population
                WHERE item_name = 'A1101_総人口')
QUALIFY ROW_NUMBER() OVER (PARTITION BY p.area ORDER BY p.value DESC) = 1  -- 内訳の重複を排除
ORDER BY population DESC LIMIT 20
```
（結合キーは双方のコード桁数を `columns` で確認して合わせる。e_stat の `area` は5桁、
lg_code は6桁の `lg_code` と5桁の `lg_code_5` がある）

## 地理: 国土数値情報（GIS）

境界ポリゴンは `geometry` カラムを持つ。spatial 拡張は自動ロード済みで `ST_*` 関数が使える:
```sql
SELECT prefecture_name, ST_Area(geometry) AS area
FROM nlftp.boundary.prefecture
ORDER BY area DESC LIMIT 10
```
（座標系は緯度経度なので面積は度単位。相対比較や地図用途向け。列名は `uvx queria columns nlftp` で確認）

## 不動産

```sql
SELECT prefecture, COUNT(*) AS deals, AVG(trade_price) AS avg_price
FROM reinfolib.main.mart_trade_prices
GROUP BY 1 ORDER BY deals DESC
```
（実カラムは `uvx queria columns reinfolib` で確認）

## 他スキルへの受け渡し（可視化・分析・ダッシュボード）

このスキルは可視化しない。結果を書き出して別スキルに渡す:
```bash
uvx queria sql "
  SELECT area_name, value FROM e_stat.ssds.a_pref_population
  WHERE item_name='A1101_総人口' AND year=2024 AND area_name<>'全国'
" --out /tmp/pref_population.parquet
```
書き出した CSV/Parquet を data:create-viz（チャート）/ data:analyze（分析）/
data:build-dashboard・Tableau/PowerBI MCP（ダッシュボード）に渡す。
