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
どんなデータセットがあるかは静的な一覧を持たず、常に `list` / `search` でカタログから取得する。

## 実行方法

queria CLI（PyPI: `queria`）を使う。uv があればインストール不要:

```bash
uvx queria list
```

uv がない場合は `pip install queria` して `queria list`。
uvx のキャッシュが古い場合は `uvx queria@latest list` で最新版を使う。

### コマンド一覧

| コマンド | 用途 |
|---|---|
| `uvx queria list` | データセット一覧 |
| `uvx queria search <キーワード>` | データセット・テーブル・カラムの横断検索（発見の起点）。`--type dataset\|table\|column` `--limit N` |
| `uvx queria info <dataset>` | メタデータ（ライセンス・出典 URL・スキーマ・更新日時）。`--readme` で README 本文も |
| `uvx queria schema <dataset>` | テーブル一覧と説明 |
| `uvx queria columns <dataset> [table]` | カラム（型・説明付き） |
| `uvx queria summarize <dataset>.<schema>.<table>` | カラム統計（件数・min/max・NULL 率）。全件スキャンなので大テーブル注意 |
| `uvx queria sql "<query>"` | read-only SQL を実行 |
| `--out <file.csv\|.parquet>` | 結果をファイルに書き出す（他スキルへの受け渡し用） |
| `--format table\|csv\|json\|jsonl\|markdown` | 標準出力の形式（既定 table、`--out` 指定時は無視） |

## 探索ワークフロー

1. 発見: `uvx queria search 人口`（何があるか分からなければ `uvx queria list`）
2. 出典確認: `uvx queria info e_stat` — ライセンスと出典 URL をここで確認できる
3. スキーマ把握: `uvx queria schema e_stat` → `uvx queria columns e_stat <table>`
4. 中身の当たり: `uvx queria sql "SELECT ... LIMIT 20"`（分布を見たいときは `summarize`）
5. 取得: `uvx queria sql "<query>"`
6. 受け渡し: 可視化・分析が必要なら `--out result.parquet` で書き出し、別スキルに渡す

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

### 定番の結合キー

データセットを跨ぐ JOIN でよく使うキー（実際の桁数・列名は `columns` で確認する）:

- `lg_code`: 全国地方公共団体コード。`lg_code.main.mart_lg_code` が結合ハブで、
  6 桁の `lg_code` と 5 桁の `lg_code_5` を持つ。e-Stat の市区町村粒度テーブルの
  `area`（5 桁）は `lg_code_5` と結合する
- `corporate_number`: 法人番号。法人系データセット同士を結合する
- `key_code`: 国勢調査小地域などの境界ポリゴンと統計値を結合する

定番クエリは `references/sql-recipes.md` を参照。

## 可視化・分析・ダッシュボード（スコープ外）

このスキルは行わない。データ取得後、目的に応じて連携する:

- グラフ・チャート: 結果を `--out result.csv` で書き出し、data:create-viz / data:data-visualization に渡す
- 統計分析・レポート: data:analyze / data:statistical-analysis に渡す
- ダッシュボード: data:build-dashboard、または Tableau/PowerBI MCP に渡す

## 制約

- 公開データ（data.queria.io）のみ・read-only。書き込み系 SQL は CLI が拒否する。
- `summarize` と絞り込みのない SELECT はリモートデータの全件スキャンになる。
  まず `LIMIT` 付きで当たりを付ける。
- DuckDB CLI で DuckLake を直接 ATTACH しない（バージョン不整合でカタログが壊れる）。
  必ず queria CLI を経由する。カタログ format が更新された場合は CLI がエラーメッセージで
  必要なアップグレードを案内する。
