# MCP Server Discovery Verification Script

Use this to test whether MCP servers installed inside Docker are actually reachable. Run after `npm install -g` to confirm tools are discovered before committing to config.yaml.

## Usage

```bash
PYTHONPATH=/workspace/pylibs python3 /home/saptarshi/.hermes/skills/devops/docker-sandbox-workarounds/scripts/verify-mcp.py
```

Or test specific servers:

```python
await test_server("PDF", "/workspace/npm-global/bin/pdf-mcp", [])
await test_server("Chrome", "/workspace/npm-global/bin/chrome-devtools-mcp", [])
await test_server("OpenWork", "/workspace/npm-global/bin/openwork-ui-mcp", [])
```

## Expected output (success)

```
✅ PDF: 34 tools
   • open_pdf: Open and read a PDF file...
   • create_pdf: Create a new blank PDF document...
   ...

✅ Chrome DevTools: 29 tools
   • click: Clicks on the provided element...
   • evaluate_script: Evaluate a JavaScript function...
   ...

✅ OpenWork UI: 4 tools
   • ui_snapshot: Get a snapshot of the current OpenWork UI state...
   ...

==================================================
SUMMARY: 3/3 passed
```

## Expected output (noexec failure)

```
❌ PDF: ExceptionGroup: unhandled errors in a TaskGroup
   → Binary downloaded but landed on noexec /tmp
   → Fix: npm install -g --prefix /workspace/npm-global
```
