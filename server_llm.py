# server_llm.py
# An MCP server with a few extra tools so an LLM-augmented client has more to choose from.
# Transport is still STDIO; run with: mcp run server.py

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo-LLM-Empowered")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract b from a"""
    return a - b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divide a by b (b must not be zero)"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

@mcp.tool()
def power(base: int, exponent: int) -> int:
    """Compute base ** exponent (integers)"""
    return base ** exponent

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

@mcp.resource("notes://{topic}")
def get_notes(topic: str) -> str:
    """Return short, read-only notes for a topic (demo resource)."""
    corpus = {
        "mcp": "MCP is a protocol that standardizes how hosts, clients, and servers exchange tools, resources, and prompts.",
        "math": "Arithmetic tools available: add, subtract, multiply, divide, power.",
        "hello": "Try the greeting resource: greeting://your-name",
    }
    return corpus.get(topic.lower(), "No notes found for this topic.")

if __name__ == "__main__":
    mcp.run()
