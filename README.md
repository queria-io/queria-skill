# Queria Skills

[日本語](README.ja.md)

A collection of [Agent Skills](https://agentskills.io/) for exploring Queria's public Japanese open data ([data.queria.io](https://queria.io)). Discover datasets, inspect schemas, run read-only SQL, and join across datasets — all in natural language from any supported agent.

Explore postal codes, NTA corporate numbers, gBizINFO, e-Stat government statistics, real estate prices, national land numerical information (GIS), municipality codes, calendars, and more, joining across independent datasets. The list of available datasets is always discovered dynamically from the catalog.

## Installation

Works with agents that support the Agent Skills standard (Claude Code, OpenAI Codex, Cursor, OpenCode, and others).

### Claude Code

Install from the [plugin marketplace](https://code.claude.com/docs/en/discover-plugins):

```
/plugin marketplace add queria-io/skills
/plugin install queria@queria-io
```

### OpenAI Codex

Install as a Codex CLI [plugin](https://developers.openai.com/codex/plugins):

```
codex plugin marketplace add queria-io/skills
codex plugin add queria@queria-io
```

### npx skills

Install into other Agent Skills-compatible agents with the [`npx skills`](https://skills.sh/) CLI:

```
npx skills add queria-io/skills
```

### Clone / Copy

You can also clone this repository and copy the skill folder into your agent's skills directory:

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
| queria | Discovering Japanese open data, inspecting schemas, read-only SQL, cross-dataset joins, CSV/Parquet export |

The skill itself lives in [skills/queria/SKILL.md](skills/queria/SKILL.md); common queries are in [references/sql-recipes.md](skills/queria/references/sql-recipes.md).

Visualization, statistical analysis, and dashboards are out of scope. Export results to CSV/Parquet and hand them to visualization/analysis skills or BI tools.

## Requirements

Uses the [queria CLI](https://docs.queria.io/) (PyPI: `queria`). With uv, `uvx queria` needs no install; otherwise `pip install queria` (Python 3.10+). No authentication required (anonymous access is [rate-limited](https://docs.queria.io/connection/authentication)).

## Environments without a shell (MCP)

From MCP clients where the agent has no shell (e.g. Claude Desktop), use the [MCP server](https://docs.queria.io/mcp) (`uvx --from 'queria[mcp]' queria mcp`) instead of the skill.

## How it works

Queria publishes each dataset as a DuckLake catalog. The queria CLI ATTACHes DuckLake read-only and queries it, just like the web app. The dataset list and all schemas are consolidated into `mart_*` tables in the `catalog` dataset, which `list` / `search` / `info` use for discovery. Compatibility between the catalog format and the CLI is managed by the CLI, which reports required upgrades in its error messages.

## License

MIT
