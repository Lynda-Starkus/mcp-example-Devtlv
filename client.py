from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    server_params = StdioServerParameters(
        command="mcp",
        args=["run", "server.py"],
        env=None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("[CLIENT] initialize")
            await session.initialize()

            # --- Discover resources properly ---
            print("[CLIENT] list resources")
            res_result = await session.list_resources()
            for r in (res_result.resources or []):
                # Each r is typically a Resource or ResourceTemplate; print what’s useful
                uri = getattr(r, "uri", None) or getattr(r, "uriTemplate", None) or r
                print("[CLIENT] Resource:", uri)

            # --- Discover tools ---
            print("[CLIENT] list tools")
            tools_result = await session.list_tools()
            for t in tools_result.tools:
                print("[CLIENT] Tool:", t.name)

            # --- Read a resource (access the contents list) ---
            print("[CLIENT] read resource greeting://hello")
            rr = await session.read_resource("greeting://hello")
            # rr.contents is a list of content parts; print text parts nicely
            for c in rr.contents:
                # c may have fields: text, uri, mimeType, etc.
                text = getattr(c, "text", None)
                mime = getattr(c, "mimeType", None)
                uri = getattr(c, "uri", None)
                if text is not None:
                    print(f"[CLIENT] Resource content: {text} (mime: {mime}, uri: {uri})")
                else:
                    print("[CLIENT] Resource part:", c)

            # --- Call a tool (extract text content) ---
            print("[CLIENT] call tool add(a=9,b=8)")
            tr = await session.call_tool("add", arguments={"a": 9, "b": 8})
            # tr.content is a list of parts (e.g., text chunks)
            for part in tr.content:
                txt = getattr(part, "text", None)
                if txt is not None:
                    print("[CLIENT] Tool result (text):", txt)
                else:
                    print("[CLIENT] Tool result (part):", part)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
