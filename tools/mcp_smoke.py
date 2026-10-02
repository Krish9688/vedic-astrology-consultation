#!/usr/bin/env python3
"""Start an MCP server command the way an MCP client (such as Claude) does, over stdio, and check that its tools
list and that a synthetic chart computes.  usage: python tools/mcp_smoke.py <command> [args...]  (default args: mcp)"""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

S1 = dict(date="1992-03-14", time="09:40", tz=0, lat=51.5, lon=-0.12)       # synthetic chart, not a person


async def main(cmd, args):
    async with stdio_client(StdioServerParameters(command=cmd, args=args or ["mcp"], env=dict(os.environ))) as (r, w), ClientSession(r, w) as s:
        init = await s.initialize()
        tools = sorted(t.name for t in (await s.list_tools()).tools)
        res = await s.call_tool("get_divisional_chart", S1 | {"division": 9})
        d9 = json.loads(res.content[0].text)["signs"]["Asc"]
        ctx = await s.call_tool("prepare_consultation", S1 | {"question": "What changes in my career?"})
        files = json.loads(ctx.content[0].text)["analysis"]["load"]
        print(f"server {init.server_info.name} {init.server_info.version}: {len(tools)} tools; D9 ascendant {d9}; "
              f"consultation routes {len(files)} skill files")
        assert d9 == "Leo" and "calculate_birth_chart" in tools and "references/topic-career-money.md" in files


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2:]))
