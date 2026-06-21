---
name: queria
description: Queria の公開オープンデータ（data.queria.io）を探索・取得する。日本の郵便番号・法人番号・統計(e-Stat)・国土数値情報・不動産・暦・自治体コードなどを read-only SQL で横断検索できる。「Queria でデータを探す/使う」「オープンデータを調べたい」「日本の○○のデータが欲しい」「データセットを横断で結合したい」などのときに使用する。可視化・分析・ダッシュボードは別スキルに渡す。
---

# Queria オープンデータ探索

Queria は日本のオープンデータを DuckLake カタログとして公開している（data.queria.io）。
このスキルはそのカタログへ read-only で接続し、データセットの発見・スキーマ把握・SQL 取得・
横断結合を行うためのもの。取得したデータの可視化・統計分析・ダッシュボード化はスコープ外で、
他スキル（data:create-viz, data:analyze, data:build-dashboard, Tableau/PowerBI MCP 等）に
`--out` で書き出して渡す。

公開データなので認証不要・ローカルビルド不要。すべて read-only で安全に実行できる。

## 利用できるデータ（2026 時点）

| dataset | 内容 |
|---|---|
| zipcode | 全国郵便番号 |
| houjin_bangou | 国税庁法人番号（約500万件） |
| gbizinfo | gBizINFO 法人活動情報（補助金・調達・財務）。houjin_bangou と結合可 |
| e_stat | e-Stat 政府統計 |
| reinfolib | 不動産価格・地価（不動産情報ライブラリ） |
| nlftp | 国土数値情報（GIS） |
| address_br | アドレス・ベース・レジストリ（市区町村マスタ） |
| lg_code | 全国地方公共団体コード |
| calendar | 日本の暦（祝日・和暦・会計年度） |
| tsukuba | つくば市オープンデータ |
| articles | Queria ショーケース記事メタデータ |

最新の一覧は必ず `--list` で取得すること（増えている可能性がある）。

## 実行方法

すべて 1 つのヘルパースクリプトで完結する。このスキルディレクトリからの相対パスで実行する:

```bash
python3 scripts/queria_query.py <オプション>
```

python3 さえあれば追加インストールは不要。初回のみ duckdb を専用ディレクトリ
（`~/.cache/queria/`）へ自動インストールする（グローバル環境は汚さない）。2 回目以降は即実行。

### コマンド一覧

| オプション | 用途 |
|---|---|
| `--list` | データセット一覧（発見の起点） |
| `--search <キーワード>` | データセットをキーワード検索 |
| `--schema <dataset>` | そのデータセットのテーブル一覧と説明 |
| `--columns <dataset>` | そのデータセットの全カラム（型・説明付き） |
| `--sql "<query>"` | read-only SQL を実行 |
| `--out <file.csv\|.parquet>` | 結果をファイルに書き出す（他スキルへの受け渡し用） |
| `--format table\|csv\|json` | 標準出力の形式（既定 table、`--out` 指定時は無視） |

## 探索ワークフロー

1. 発見: `python3 scripts/queria_query.py --list`（または `--search 不動産`）
2. スキーマ把握: `python3 scripts/queria_query.py --schema reinfolib`
3. カラム確認: `python3 scripts/queria_query.py --columns reinfolib`
4. 取得: `python3 scripts/queria_query.py --sql "SELECT ... LIMIT 50"`
5. 受け渡し: 可視化・分析が必要なら `--out result.parquet` で書き出し、別スキルに渡す

### SQL の書き方

テーブルは `データセット名.スキーマ.テーブル名` で参照する（例: `zipcode.main.mart_zipcode`）。
各データセットは別カタログだが、複数を参照すれば自動でアタッチされ横断結合できる。
分析向けの整形済みテーブルは `mart_` 接頭辞（`raw_` は生データ、`stg_` は中間）。

横断結合の例（郵便番号 × 自治体コード）:

```sql
SELECT g.prefecture, g.city, COUNT(*) AS zip_count
FROM zipcode.main.mart_zipcode z
JOIN lg_code.main.mart_lg_code g ON z.lg_code = g.lg_code
GROUP BY 1, 2 ORDER BY zip_count DESC
```

定番クエリは `references/sql-recipes.md`、データセット詳細は `references/datasets.md` を参照。

## 可視化・分析・ダッシュボード（スコープ外）

このスキルは行わない。データ取得後、目的に応じて連携する:

- グラフ・チャート: 結果を `--out result.csv` で書き出し、data:create-viz / data:data-visualization に渡す
- 統計分析・レポート: data:analyze / data:statistical-analysis に渡す
- ダッシュボード: data:build-dashboard、または Tableau/PowerBI MCP に渡す

## 制約

- 公開データ（data.queria.io）のみ・read-only。書き込み系 SQL はスクリプトが拒否する。
- duckdb は DuckLake v1（カタログ format 1.0）に対応する版（1.5.4+）にピンしている。
  Queria 側のカタログ format が上がったら `scripts/queria_query.py` の `DUCKDB_SPEC` /
  `MIN_DUCKDB` を更新すること。
- DuckDB CLI で DuckLake を直接 ATTACH しない（バージョン不整合でカタログが壊れる）。
  必ずこのスクリプト（バージョン固定済みの Python duckdb）を経由する。
