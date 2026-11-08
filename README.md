# mcp-suite

Minimal Model Context Protocol server over stdio - project #3 ("MCP Server
Suite") from the TOP 1% AI projects list. Exposes your own tools to any
MCP-compatible client (Claude Desktop, an IDE, your own agent) through the
standard JSON-RPC protocol instead of bespoke glue code.

## What it does

- **protocol**: newline-delimited JSON-RPC 2.0 stdio transport plus the MCP
  handshake (`initialize`) and tool surface (`tools/list`, `tools/call`).
  Notifications, malformed JSON and tool failures are handled per spec.
- **tools** (stdlib-only, sandboxed):
  - `read_file` - read a UTF-8 file inside a sandboxed root (path-escape safe)
  - `route_cost` - cheapest-capable model pick, from sibling `cost-router`
  - `grade_trajectory` - golden-trajectory grading, from sibling `trajectory-eval`
- Sibling imports are lazy: the server still runs where they are absent.

## Run it

```bash
python -m mcpsuite.server        # then speak JSON-RPC on stdin
{"jsonrpc": "2.0", "id": 1, "method": "initialize"}
{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "route_cost", "arguments": {"prompt": "hello"}}}
```

## Test

```bash
python -m unittest discover -s tests
```

11 tests cover the handshake, tool listing/calling, sandbox escape rejection,
the stdio loop (including malformed JSON and tool-error paths).

## Scope

Deterministic and offline. This is the plumbing layer: point a real MCP
client at it to give an agent audited, budget-aware tools (see `cost-router`,
`trajectory-eval`, `agent-lab`).

## Demo

`demo.py` reproduces the recorded demo run end to end, offline (standard
library only, no model calls):

    python demo.py

It executes the library's real code path and prints the same output shown in
the recorded demo video.
