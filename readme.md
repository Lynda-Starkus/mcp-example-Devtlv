# MCP Starter — GitHub Codespaces (Python)

This repo runs a **Model Context Protocol** server and client inside **GitHub Codespaces** with one click.

## What’s included
- `server.py` — minimal MCP server (tool `add`, resource `greeting://{name}`)
- `client.py` — MCP client that spawns the server over **STDIO**, discovers features, and invokes them
- `requirements.txt` — installs `mcp[cli]`
- `.devcontainer/devcontainer.json` — auto-creates a Python 3.11 venv and installs deps; adds Node (for Inspector)
- `.vscode/settings.json` — points VS Code to the venv interpreter
- `package.json` — `npm run inspector` convenience script (optional)

## Open in Codespaces
1. Push these files to a GitHub repo.
2. Click **Code → Codespaces → Create codespace on main**.
3. Wait for the container to build (the venv + deps are installed automatically).

> If installation failed or you want to reinstall, run:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run & test the MCP locally (inside Codespaces)

### Option A — Two terminals (classic “local” feel)
Open two terminals in VS Code (Terminal → “+”):

**Terminal 1 — Server + Inspector (optional UI)**
```bash
# Start server alone (STDIO, no UI)
mcp run server.py

# OR: start server *and* Inspector UI (will open a forwarded port)
npm run inspector
```
> If you start Inspector, accept the port-forward prompt in Codespaces to open the web UI. You can list tools/resources and call them interactively.

**Terminal 2 — Client**
```bash
source .venv/bin/activate
python client.py
```

### Option B — One terminal (client spawns server)
```bash
source .venv/bin/activate
python client.py
```
The client launches the server via the MCP CLI and prints discovery + invocation results.

## Expected output (client)
```
[CLIENT] initialize
[CLIENT] list resources
[CLIENT] Resource: ...
[CLIENT] list tools
[CLIENT] Tool: add
[CLIENT] read resource greeting://hello
[CLIENT] Resource content: Hello, hello! mime_type: text/plain
[CLIENT] call tool add(a=1,b=7)
[CLIENT] Tool result: [...]
```

## How it works
- **Transport:** STDIO via `mcp run server.py` — no TCP port needed for local dev.
- **Discovery:** `list_resources()` and `list_tools()` enumerate capabilities.
- **Invocation:** `read_resource(uri)` for read-only context; `call_tool(name, args)` for actions.

## Troubleshooting
- **`mcp: command not found`** — ensure the venv is active (`source .venv/bin/activate`) so the `mcp` CLI is on your PATH.
- **Server isn’t visible in Inspector** — did you start Inspector with `npm run inspector` (or `mcp dev server.py`)? Accept the forwarded port prompt.
- **Type/arg errors** — ensure your tool arguments match the server signature (e.g., `{ "a": 1, "b": 7 }`).

## Next steps
- Add more tools/resources to `server.py` and rerun `npm run inspector` to see them immediately.
- Keep the client simple, or build an LLM loop that decides when to read/call.
