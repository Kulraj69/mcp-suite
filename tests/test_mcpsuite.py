import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcpsuite.protocol import McpServer, JsonRpcPeer
from mcpsuite.tools import TOOLS, read_file
from mcpsuite import server as srv


def make_server():
    return McpServer("mcp-suite", "0.1.0", TOOLS)


class TestProtocol(unittest.TestCase):
    def test_initialize(self):
        rid, res = make_server().handle({"id": 1, "method": "initialize"})
        self.assertEqual(res["serverInfo"]["name"], "mcp-suite")
        self.assertIn("protocolVersion", res)

    def test_tools_list(self):
        rid, res = make_server().handle({"id": 2, "method": "tools/list"})
        names = [t["name"] for t in res["tools"]]
        self.assertIn("read_file", names)
        self.assertIn("route_cost", names)
        self.assertIn("grade_trajectory", names)
        for t in res["tools"]:
            self.assertIn("inputSchema", t)

    def test_unknown_method(self):
        with self.assertRaises(LookupError):
            make_server().handle({"id": 3, "method": "nope"})

    def test_unknown_tool(self):
        with self.assertRaises(LookupError):
            make_server().handle({"id": 4, "method": "tools/call",
                                  "params": {"name": "nope", "arguments": {}}})


class TestTools(unittest.TestCase):
    def test_read_file_in_sandbox(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "hello.txt")
            open(p, "w").write("hi there")
            self.assertEqual(read_file("hello.txt", root=td), "hi there")

    def test_read_file_blocks_escape(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                read_file("../outside.txt", root=td)

    def test_route_cost_tool(self):
        from mcpsuite.tools import route_cost
        out = route_cost("hello")
        self.assertIn("local-7b", out)

    def test_grade_trajectory_tool(self):
        from mcpsuite.tools import grade_trajectory
        ex = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "..", "trajectory-eval", "examples", "golden.jsonl")
        if not os.path.exists(ex):
            self.skipTest("sibling trajectory-eval examples not present")
        out = grade_trajectory(os.path.abspath(ex))
        self.assertIn("score", out.lower())


class TestStdioLoop(unittest.TestCase):
    def _run(self, lines):
        inp = io.StringIO("\n".join(json.dumps(l) for l in lines) + "\n")
        out = io.StringIO()
        srv.main(inp, out)
        out.seek(0)
        return [json.loads(l) for l in out if l.strip()]

    def test_full_conversation(self):
        resps = self._run([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "route_cost", "arguments": {"prompt": "write a function"}}},
        ])
        self.assertEqual(len(resps), 3)  # notification got no reply
        self.assertEqual(resps[0]["id"], 1)
        self.assertIn("tools", resps[1]["result"])
        self.assertIn("mid-general", resps[2]["result"]["content"][0]["text"])

    def test_bad_json_reports_error(self):
        inp = io.StringIO("{not json\n")
        out = io.StringIO()
        srv.main(inp, out)
        out.seek(0)
        resps = [json.loads(l) for l in out if l.strip()]
        self.assertEqual(resps[0]["error"]["code"], -32700)

    def test_tool_error_is_internal_error(self):
        resps = self._run([
            {"jsonrpc": "2.0", "id": 9, "method": "tools/call",
             "params": {"name": "read_file", "arguments": {"path": "/nope/nothing.txt"}}},
        ])
        self.assertEqual(resps[0]["error"]["code"], -32603)


if __name__ == "__main__":
    unittest.main()
