"""Reproduces the demo video's real output: JSON-RPC roundtrips."""
from mcpsuite.server import McpServer
from mcpsuite.tools import TOOLS

REQS = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "route_cost", "arguments": {"prompt": "Summarize this 3-line email in one sentence."}}},
    {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "read_file", "arguments": {"path": "../../etc/passwd"}}},
]
if __name__ == "__main__":
    srv = McpServer("mcp-suite", "0.1.0", TOOLS)
    for q in REQS:
        print("->", q["method"], (q.get("params") or {}).get("name", ""))
        try:
            print("<-", srv.handle(q))
        except Exception as e:
            print(f"<- error: {type(e).__name__}: {e}")
