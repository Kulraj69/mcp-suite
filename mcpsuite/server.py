"""Entry point: run the MCP stdio server.

    python -m mcpsuite.server          # speaks JSON-RPC on stdin/stdout
"""

import sys

from .protocol import INTERNAL_ERROR, METHOD_NOT_FOUND, INVALID_PARAMS, JsonRpcPeer, McpServer
from .tools import TOOLS


def main(instream=None, outstream=None) -> int:
    peer = JsonRpcPeer(instream or sys.stdin, outstream or sys.stdout)
    server = McpServer("mcp-suite", "0.1.0", TOOLS)
    for req in peer.requests():
        try:
            rid, result = server.handle(req)
            peer.reply(rid, result)
        except LookupError as e:
            peer.error(req.get("id"), METHOD_NOT_FOUND, str(e))
        except TypeError as e:
            peer.error(req.get("id"), INVALID_PARAMS, str(e))
        except Exception as e:  # tool errors are reported, not fatal
            peer.error(req.get("id"), INTERNAL_ERROR, str(e))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
