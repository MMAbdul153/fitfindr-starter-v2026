"""
Your MCP server. ← UNIT 4, MILESTONE 1

Right now your tools only exist inside your own program. Nothing else can reach
them. MCP is an agreed shape you wrap a tool in so that anything speaking the
same protocol can call it — your agent today, a different agent tomorrow,
someone else's app after that.

**You're moving one tool. Not three.** The point is to see the seam.
`search_listings` is the one to move: it doesn't call the model, so nothing is
slow and nothing changes between runs while you're learning the shape.

    python mcp_server.py        starts the server (it will just sit there — that's right)
    python mcp_client.py        asks the server what it offers
"""

from mcp.server.fastmcp import FastMCP

from tools import search_listings as _search_listings_impl  # noqa: F401 — you'll use this below


# log_level="WARNING" keeps the server from printing an INFO line for every
# request. Without it your terminal fills with "Processing request of type
# CallToolRequest" and the output you actually care about scrolls away.
mcp = FastMCP("fitfindr", log_level="WARNING")


# ── Registered MCP Tool ───────────────────────────────────────────────────────

@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Searches the second-hand listings dataset for clothing items matching
    keywords in the description, an optional size filter (e.g., 'M', 'L'), and
    an optional maximum price ceiling (in dollars).

    Returns a list of matching listing dictionaries containing title, price,
    size, platform, and description. Returns an empty list [] if no items match.
    """
    return _search_listings_impl(description, size, max_price)


if __name__ == "__main__":
    mcp.run()