"""JSON-RPC 2.0 over stdio, the transport MCP speaks.

One JSON object per line (newline-delimited JSON), which is how the reference
MCP stdio transport frames messages. Handles requests (id present) and
ignores notifications (no id) beyond acknowledging them.
"""

import json

PARSE_ERROR = -32700
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class JsonRpcPeer:
    def __init__(self, instream, outstream):
        self._in = instream
        self._out = outstream

    def _send(self, obj):
        self._out.write(json.dumps(obj) + "\n")
        self._out.flush()

    def reply(self, req_id, result):
        self._send({"jsonrpc": "2.0", "id": req_id, "result": result})

    def error(self, req_id, code, message):
        self._send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})

    def requests(self):
        """Yield decoded request objects; skip blank lines and notifications."""
        for line in self._in:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                self.error(None, PARSE_ERROR, "invalid JSON")
                continue
            if "id" not in obj:      # notification: acknowledge silently
                continue
            yield obj


class McpServer:
    """Minimal MCP server: initialize, tools/list, tools/call."""

    PROTOCOL_VERSION = "2024-11-05"

    def __init__(self, name, version, tools):
        # tools: list of (name, description, inputSchema, callable)
        self.name = name
        self.version = version
        self._tools = {t[0]: t for t in tools}

    def handle(self, req):
        method = req.get("method")
        rid = req.get("id")
        if method == "initialize":
            return rid, {"protocolVersion": self.PROTOCOL_VERSION,
                         "serverInfo": {"name": self.name, "version": self.version},
                         "capabilities": {"tools": {}}}
        if method == "tools/list":
            return rid, {"tools": [
                {"name": n, "description": t[1], "inputSchema": t[2]}
                for n, t in self._tools.items()]}
        if method == "tools/call":
            params = req.get("params") or {}
            tool = self._tools.get(params.get("name"))
            if tool is None:
                raise LookupError(f"unknown tool: {params.get('name')}")
            out = tool[3](**(params.get("arguments") or {}))
            return rid, {"content": [{"type": "text", "text": str(out)}]}
        raise LookupError(f"unknown method: {method}")
