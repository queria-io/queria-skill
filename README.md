# Queria Skills

Queria が公開する日本のオープンデータ（[data.queria.io](https://queria.io)）を探索するための [Agent Skills](https://agentskills.io/) コレクション。データセットの発見・スキーマ把握・read-only SQL・横断結合を、対応エージェントから自然言語で行える。

郵便番号、国税庁法人番号、gBizINFO、e-Stat 政府統計、不動産価格、国土数値情報（GIS）、自治体コード、暦などを、別々のデータセットを跨いで JOIN しながら探索できる。利用できるデータセットの一覧は常にカタログから動的に取得する。

## インストール

Agent Skills 標準に対応したエージェント（Claude Code、OpenAI Codex、Cursor、OpenCode など）で利用できる。

### Claude Code

[プラグインマーケットプレイス](https://code.claude.com/docs/en/discover-plugins)からインストールする:

```
/plugin marketplace add queria-io/skills
/plugin install queria@queria-io
```

### OpenAI Codex

Codex CLI の[プラグイン](https://developers.openai.com/codex/plugins)としてインストールする:

```
codex plugin marketplace add queria-io/skills
codex plugin add queria@queria-io
```

### npx skills

[`npx skills`](https://skills.sh/) CLI で、その他の Agent Skills 対応エージェントにインストールする:

```
npx skills add queria-io/skills
```

### Clone / Copy

このリポジトリを clone して、スキルフォルダをエージェントのスキルディレクトリにコピーしてもよい:

| Agent | Skill Directory | Docs |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | [docs](https://code.claude.com/docs/en/skills) |
| Cursor | `~/.cursor/skills/` | [docs](https://cursor.com/docs/context/skills) |
| OpenCode | `~/.config/opencode/skills/` | [docs](https://opencode.ai/docs/skills/) |
| OpenAI Codex | `~/.codex/skills/` | [docs](https://developers.openai.com/codex/skills/) |
| Pi | `~/.pi/agent/skills/` | [docs](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent#skills) |

## Skills

| Skill | Useful for |
| --- | --- |
| queria | 日本のオープンデータの発見・スキーマ把握・read-only SQL・横断結合・CSV/Parquet 書き出し |

スキルの本体は [skills/queria/SKILL.md](skills/queria/SKILL.md)、定番クエリは [references/sql-recipes.md](skills/queria/references/sql-recipes.md) を参照。

可視化・統計分析・ダッシュボードはスコープ外。取得結果を CSV/Parquet に書き出し、可視化・分析用の別スキルや BI ツールに渡す。

## 必要なもの

[queria CLI](https://docs.queria.io/)（PyPI: `queria`）を使う。uv があれば `uvx queria` でインストール不要、なければ `pip install queria`（Python 3.10+）。認証は不要（匿名アクセスには[レートリミット](https://docs.queria.io/connection/authentication)がある）。

## シェルの無い環境（MCP）

Claude Desktop など、エージェントがシェルを使えない MCP クライアントからはスキルの代わりに [MCP サーバー](https://docs.queria.io/mcp)（`uvx --from 'queria[mcp]' queria mcp`）を使う。

## 仕組み

Queria は各データセットを DuckLake カタログとして公開している。queria CLI が Web 版と同じく DuckLake を read-only で ATTACH してクエリする。データセット一覧と全スキーマは `catalog` データセットの `mart_*` テーブルに統合されており、`list` / `search` / `info` はここから発見する。カタログ format と CLI の互換性は CLI 側が管理し、更新が必要な場合はエラーメッセージで案内される。

## License

MIT
