# Queria Open Data skill

Claude Code / エージェント向けのスキル。Queria が公開する日本のオープンデータ
（data.queria.io）に read-only で接続し、データセットの発見・スキーマ把握・SQL 取得・
横断結合を超簡単に行えるようにする。

郵便番号、国税庁法人番号、gBizINFO、e-Stat 政府統計、不動産価格、国土数値情報（GIS）、
自治体コード、暦などを、別々のデータセットを跨いで JOIN しながら探索できる。

可視化・統計分析・ダッシュボードはこのスキルのスコープ外。取得結果を CSV/Parquet に
書き出し、data:create-viz / data:analyze / Tableau・PowerBI MCP などの別スキルに渡す。

## 必要なもの

python3 のみ。初回実行時に duckdb を専用ディレクトリ（`~/.cache/queria/`）へ自動
インストールするため、事前インストールやグローバル環境への影響はない。公開データなので
認証も不要。

## インストール

プラグインとして:

```bash
# ローカルディレクトリから（開発・お試し）
claude --plugin-dir /path/to/queria-skill

# マーケットプレイス経由（公開後）
claude plugin install queria@<marketplace>
```

単一スキルとして（手軽に試す）:

```bash
ln -s /path/to/queria-skill/skills/queria ~/.claude/skills/queria
```

## 使い方

エージェントに「Queria で東京都の郵便番号を調べて」「日本の都道府県別人口を出して」などと
頼めばスキルが起動する。直接実行する場合:

```bash
cd skills/queria
python3 scripts/queria_query.py --list                  # データセット一覧
python3 scripts/queria_query.py --schema e_stat         # テーブル一覧
python3 scripts/queria_query.py --columns zipcode       # カラム一覧
python3 scripts/queria_query.py --sql "SELECT ... LIMIT 50"
python3 scripts/queria_query.py --out result.parquet --sql "..."   # 書き出し
```

詳細は [skills/queria/SKILL.md](skills/queria/SKILL.md)、データセットは
[references/datasets.md](skills/queria/references/datasets.md)、定番クエリは
[references/sql-recipes.md](skills/queria/references/sql-recipes.md) を参照。

## 仕組み

Queria は各データセットを DuckLake カタログとして公開している。スクリプトは Web 版と同じく
DuckLake を read-only で ATTACH してクエリする。データセット一覧と全スキーマは `catalog`
データセットの `mart_*` テーブルに統合されており、ここから発見する。

公開カタログは DuckLake v1（format 1.0）。これを読める duckdb 1.5.4+ にピンしている。
Queria 側のカタログ format が上がった場合は `scripts/queria_query.py` の `DUCKDB_SPEC` /
`MIN_DUCKDB` を更新する。
