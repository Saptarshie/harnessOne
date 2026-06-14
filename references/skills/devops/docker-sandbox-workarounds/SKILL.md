---
name: docker-sandbox-workarounds
description: "Work around Docker container restrictions: noexec mounts, npm cache permissions, writable filesystem discovery, persistent vs ephemeral storage. Use when a tool fails with 'Permission denied' on execution, npm can't write cache, or you need to install persistent binaries inside a locked-down container."
version: 1.0.0
metadata:
  hermes:
    tags: [docker, sandbox, workarounds, npm, noexec, persistence, troubleshooting]
---

# Docker Sandbox Workarounds

Hermes's terminal backend runs inside a Docker container with security restrictions not present on a normal Linux system. When tools unexpectedly fail with "Permission denied" or write errors, the cause is usually one of these container quirks — not a broken tool.

## Trigger

Load this skill when:
- A binary fails with `Permission denied` immediately after download (npx, pip, go install)
- npm errors with `EACCES` on `/.npm` or `/.npmrc`
- A script refuses to run from `/tmp` or `/var/tmp` despite `chmod +x`
- You need binaries or data to survive across sessions
- `pip install`, `npm install -g`, or `apt-get install` fails with permission errors

## Core Diagnosis: Find the Executable Filesystem

The root cause of most failures is `noexec` mounts. Diagnose in this order:

### Step 1 — Check mount flags

```bash
mount | grep -E "tmp|noexec"
```

Key mounts to watch:
- `/tmp` — almost always `noexec` in Docker
- `/var/tmp` — usually `noexec`
- `/run` — usually `noexec`
- `/dev/shm` — sometimes `noexec`

### Step 2 — Find a writable + executable filesystem

```bash
# Test execution
echo 'echo OK' > /workspace/_test.sh && chmod +x /workspace/_test.sh && /workspace/_test.sh && rm /workspace/_test.sh
```

The `/workspace` directory (mapped from the host via 9p or bind mount) is typically writable and executable. It is also **persistent** across container restarts — it survives session boundaries.

### Step 3 — Redirect tool output to the safe filesystem

| Tool | Default cache/target | Redirect to |
|------|---------------------|-------------|
| npx | `/tmp/npm-cache/_npx/` | Install globally to `/workspace/npm-global/` |
| npm | `/.npm` (root-owned) | Set `npm_config_cache=/workspace/npm-cache` |
| pip | system site-packages (permission denied) | `pip install --target=/workspace/pylibs` |
| go build | `GOPATH` default | `export GOPATH=/workspace/go` |

## Recipe: npm/npx Workaround (Most Common)

This is the most frequent failure pattern. npx downloads binaries to `/tmp` which is `noexec`, so they can never run.

### Symptoms

```
$ npx -y some-mcp-server
sh: 1: some-mcp-server: Permission denied
```

npm also fails with:
```
npm error code EACCES
npm error path /.npm
```

### Fix — Global Install to /workspace

```bash
# 1. Configure npm to use /workspace
export npm_config_cache=/workspace/npm-cache
export npm_config_prefix=/workspace/npm-global
export PATH="/workspace/npm-global/bin:$PATH"
mkdir -p /workspace/npm-cache /workspace/npm-global

# 2. Install globally (not npx)
npm install -g <package-name>

# 3. Use the direct binary path
/workspace/npm-global/bin/<binary-name>
```

Binaries installed this way survive across sessions because `/workspace` is a persistent host mount.

### Why This Works

```
npx fails:  download → /tmp (noexec) → kernel blocks execution
npm -g OK:  download → /workspace/npm-global (executable) → kernel allows
```

The binary lands on a filesystem without the `noexec` mount flag.

### Using These Binaries in MCP Config

Once installed, use direct paths in `config.yaml` instead of npx:

```yaml
mcp_servers:
  my_server:
    command: "/workspace/npm-global/bin/my-server"
    args: []
```

This is Docker-proof: no npx, no /tmp, no ephemeral cache.

## Recipe: pip Workaround

```bash
# Global pip fails with permission errors
pip install some-package --target=/workspace/pylibs

# Then use with PYTHONPATH
PYTHONPATH=/workspace/pylibs python3 -c "import some_package"
```

## Recipe: Persistent Storage

| Location | Persists? | Use for |
|----------|-----------|---------|
| `/workspace/` | ✅ Yes (host mount) | Binaries, data, projects, pip packages, npm global installs |
| `/tmp/` | ❌ Wiped each session | Throwaway temporary files only |
| `/run/` | ❌ Wiped each session | Nothing persistent |
| `~/.npm` | ❌ Wiped each session | Don't rely on npm cache here |
| `/usr/local/` | ❌ Wiped each session | Don't install system packages |

## Recipe: Verifying MCP Server Installation

After installing MCP servers globally, verify with the Python MCP client:

```python
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def test():
    server_params = StdioServerParameters(
        command="/workspace/npm-global/bin/pdf-mcp", args=[]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"{len(tools.tools)} tools discovered")
            for t in tools.tools:
                print(f"  {t.name}")

asyncio.run(test())
```

## Pitfalls

- **Don't bother with `chmod +x` on noexec mounts** — the execute bit is set at the filesystem level, but the kernel-level `noexec` flag overrides it. The only fix is moving to a non-noexec filesystem.
- **Don't set npm config via `npm config set`** — the global `/.npmrc` is root-owned. Use environment variables instead: `npm_config_cache`, `npm_config_prefix`.
- **Don't use `sudo`** — you're running as an unprivileged user inside the container and `sudo` is typically not available.
- **Don't assume files in `/tmp` are still there** across tool calls — the container may reuse `/tmp` between calls.
- **`apt-get install` almost always fails** — the container is locked down. Find alternative install methods (pip --target, npm -g with prefix, static binaries, uv/uvx).
