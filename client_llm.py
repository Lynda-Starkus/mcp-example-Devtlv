# client_llm.py
# Connects to server_llm.py over STDIO, discovers tool schemas,
# exposes them to an LLM (if available) or uses a tiny rule-based fallback,
# then executes the proposed tool calls and prints results.

import os
import re
import json
from typing import List, Dict, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def convert_to_llm_tool(tool) -> Dict[str, Any]:
    """Convert MCP tool metadata to a function-calling schema for LLMs."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "type": "function",
            "parameters": {
                "type": "object",
                "properties": tool.inputSchema.get("properties", {})
            }
        }
    }

def try_call_llm(prompt: str, functions: List[Dict[str, Any]]):
    """Attempt to call an LLM that supports function calling.
    If the Azure AI Inference SDK is unavailable, fall back to a simple rule-based parser.
    """
    try:
        from azure.ai.inference import ChatCompletionsClient
        from azure.core.credentials import AzureKeyCredential
    except Exception:
        print("[CLIENT] Azure AI Inference not installed; using rule-based fallback.")
        return rule_based_tool_selector(prompt, functions)

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[CLIENT] GITHUB_TOKEN not set; using rule-based fallback.")
        return rule_based_tool_selector(prompt, functions)

    endpoint = "https://models.inference.ai.azure.com"
    model_name = "gpt-4o"

    try:
        client = ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(token))
        print("[CLIENT] Calling LLM for tool selection...")
        resp = client.complete(
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Prefer tools when appropriate."},
                {"role": "user", "content": prompt},
            ],
            model=model_name,
            tools=functions,
            temperature=0.2,
            max_tokens=400,
            top_p=1.0,
        )
        msg = resp.choices[0].message
        chosen = []
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments or "{}")
                chosen.append({"name": name, "args": args})
        return chosen
    except Exception as e:
        print(f"[CLIENT] LLM call failed ({e}); using rule-based fallback.")
        return rule_based_tool_selector(prompt, functions)

def rule_based_tool_selector(prompt: str, functions: List[Dict[str, Any]]):
    """Very small deterministic parser so the demo works without an LLM provider."""
    text = prompt.lower().strip()

    def fn_available(name: str) -> bool:
        return any(f.get("function", {}).get("name") == name for f in functions)

    # add: "add 2 and 3" / "add 2 to 3"
    m = re.search(r"add\s+(\-?\d+)\s+(?:and|to)\s+(\-?\d+)", text)
    if m and fn_available("add"):
        a, b = int(m.group(1)), int(m.group(2))
        return [{"name": "add", "args": {"a": a, "b": b}}]

    # multiply: "multiply 7 by 6"
    m = re.search(r"multiply\s+(\-?\d+)\s+by\s+(\-?\d+)", text)
    if m and fn_available("multiply"):
        a, b = int(m.group(1)), int(m.group(2))
        return [{"name": "multiply", "args": {"a": a, "b": b}}]

    # subtract: "subtract 5 from 12"
    m = re.search(r"subtract\s+(\-?\d+)\s+from\s+(\-?\d+)", text)
    if m and fn_available("subtract"):
        b, a = int(m.group(1)), int(m.group(2))  # note order
        return [{"name": "subtract", "args": {"a": a, "b": b}}]

    # divide: "divide 20 by 4"
    m = re.search(r"divide\s+(\-?\d+)\s+by\s+(\-?\d+)", text)
    if m and fn_available("divide"):
        a, b = int(m.group(1)), int(m.group(2))
        return [{"name": "divide", "args": {"a": a, "b": b}}]

    # power: "power 2 to 10" or "2 to the power of 10"
    m = re.search(r"power\s+(\-?\d+)\s+(?:to|of)\s+(\-?\d+)", text)
    if m and fn_available("power"):
        base, exponent = int(m.group(1)), int(m.group(2))
        return [{"name": "power", "args": {"base": base, "exponent": exponent}}]

    # greeting: "greet alice" -> read resource
    m = re.search(r"greet\s+([a-zA-Z0-9_\-]+)", text)
    if m:
        # We'll express this as a pseudo-call the runner understands
        return [{"name": "__read_resource__", "args": {"uri": f"greeting://{m.group(1)}"}}]

    # notes: "show notes about mcp"
    m = re.search(r"notes?\s+(?:about|on)\s+([a-zA-Z0-9_\-]+)", text)
    if m:
        return [{"name": "__read_resource__", "args": {"uri": f"notes://{m.group(1)}"}}]

    # default: no tool
    return []

async def main():
    # 1) Connect via STDIO, spawning the empowered server
    server_params = StdioServerParameters(
        command="mcp",
        args=["run", "server_llm.py"],
        env=None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("[CLIENT] initialize")
            await session.initialize()

            print("[CLIENT] discover tools")
            tools_result = await session.list_tools()
            functions = [convert_to_llm_tool(t) for t in tools_result.tools]
            for t in tools_result.tools:
                print(" -", t.name)

            # 2) Ask the (LLM or fallback) what to do
            prompt = os.environ.get("MCP_DEMO_PROMPT", "add 2 and 20")
            print(f"[CLIENT] prompt: {prompt}")
            chosen = try_call_llm(prompt, functions)

            if not chosen:
                print("[CLIENT] No tool/resource selected by LLM/fallback.")
                return

            # 3) Execute tool calls / resource reads
            for call in chosen:
                name = call["name"]
                args = call["args"]
                if name == "__read_resource__":
                    uri = args.get("uri")
                    print(f"[CLIENT] read resource {uri}")
                    rr = await session.read_resource(uri)
                    for c in rr.contents:
                        txt = getattr(c, "text", None)
                        if txt is not None:
                            print("[CLIENT] Resource content:", txt)
                        else:
                            print("[CLIENT] Resource part:", c)
                else:
                    print(f"[CLIENT] call tool {name}({args})")
                    tr = await session.call_tool(name, arguments=args)
                    for part in tr.content:
                        txt = getattr(part, "text", None)
                        if txt is not None:
                            print("[CLIENT] Tool result (text):", txt)
                        else:
                            print("[CLIENT] Tool result (part):", part)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
