#!/usr/bin/env python3
"""Verify MCP servers installed in Docker are reachable and list their tools."""
import asyncio, sys, os

sys.path.insert(0, '/workspace/pylibs')

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def test_server(label: str, command: str, args: list[str]) -> bool:
    server_params = StdioServerParameters(command=command, args=args)
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=15)
                tools = await asyncio.wait_for(session.list_tools(), timeout=10)
                print(f"\n✅ {label}: {len(tools.tools)} tools")
                for t in tools.tools:
                    desc = (t.description or '')[:100]
                    print(f"   • {t.name}: {desc}")
                return True
    except Exception as e:
        print(f"\n❌ {label}: {type(e).__name__}: {str(e)[:150]}")
        return False

async def main():
    servers = [
        ("PDF", "/workspace/npm-global/bin/pdf-mcp", []),
        ("Chrome DevTools", "/workspace/npm-global/bin/chrome-devtools-mcp", []),
        ("OpenWork UI", "/workspace/npm-global/bin/openwork-ui-mcp", []),
    ]
    
    results = {}
    for label, cmd, args in servers:
        if os.path.exists(cmd):
            results[label] = await test_server(label, cmd, args)
        else:
            print(f"\n⚠️  {label}: binary not found at {cmd}")
            results[label] = False
    
    passed = sum(results.values())
    total = len(results)
    print(f"\n{'='*50}")
    print(f"SUMMARY: {passed}/{total} passed")
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
