# Queria Claude Code plugin

Queria 公式の Claude Code プラグイン。Queria が公開する日本のオープンデータ
（data.queria.io）に read-only で接続し、データセットの発見・スキーマ把握・SQL 取得・
横断結合を行うスキルを提供する。

郵便番号、国税庁法人番号、gBizINFO、e-Stat 政府統計、不動産価格、国土数値情報（GIS）、
自治体コード、暦などを、別々のデータセットを跨いで JOIN しながら探索できる。
利用できるデータセットの一覧は常にカタログから動的に取得する。

可視化・統計分析・ダッシュボードはこのスキルのスコープ外。取得結果を CSV/Parquet に
書き出し、data:create-viz / data:analyze / Tableau・PowerBI MCP などの別スキルに渡す。

## 必要なもの

[queria CLI](https://docs.queria.io/)（PyPI: `queria`）を使う。uv があれば
`uvx queria` でインストール不要、なければ `pip install queria`（Python 3.10+）。
公開データなので認証は不要。

## インストール

```bash
claude plugin marketplace add queria-io/claude-plugin
claude plugin install queria@queria-io
```

ローカルディレクトリから試す場合:

```bash
claude --plugin-dir /path/to/claude-plugin
```

旧 `queria@flo8s`（リポジトリ名 queria-skill）からの移行は、マーケットプレイスを
`queria-io/claude-plugin` で追加し直してからインストールする。

## 使い方

エージェントに「Queria で東京都の郵便番号を調べて」「日本の都道府県別人口を出して」などと
頼めばスキルが起動する。直接実行する場合:

```bash
uvx queria list                              # データセット一覧
uvx queria search 人口                        # データセット・テーブル・カラムの横断検索
uvx queria info e_stat                       # メタデータ（ライセンス・出典など）
uvx queria schema e_stat                     # テーブル一覧
uvx queria columns zipcode                   # カラム一覧
uvx queria sql "SELECT ... LIMIT 50"
uvx queria sql "..." --out result.parquet    # 書き出し
```

詳細は [skills/queria/SKILL.md](skills/queria/SKILL.md)、定番クエリは
[references/sql-recipes.md](skills/queria/references/sql-recipes.md) を参照。

## 仕組み

Queria は各データセットを DuckLake カタログとして公開している。queria CLI が Web 版と
同じく DuckLake を read-only で ATTACH してクエリする。データセット一覧と全スキーマは
`catalog` データセットの `mart_*` テーブルに統合されており、`list` / `search` / `info` は
ここから発見する。カタログ format と CLI の互換性は CLI 側が管理し、更新が必要な場合は
エラーメッセージで案内される。

## License

MIT
