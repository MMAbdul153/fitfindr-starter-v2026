"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re
from typing import Optional, Tuple
import config
import trace
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable
from mcp_client import call_tool


# ── query parser ─────────────────────────────────────────────────────────────


def parse_query_params(query: str) -> Tuple[str, Optional[str], Optional[float]]:
    """
    Parses the user query into description keywords, optional size, and max price.
    Examples:
      - "vintage graphic tee under $30, size M" -> ("vintage graphic tee", "M", 30.0)
      - "leather trench coat under $5" -> ("leather trench coat", None, 5.0)
    """
    # 1. Extract maximum price (matches e.g. "under $30", "under 30", "$30", "< $50")
    max_price = None
    price_match = re.search(r'(?:under|<|\$)\s*(\d+(?:\.\d+)?)', query, re.IGNORECASE)
    if price_match:
        try:
            max_price = float(price_match.group(1))
        except (ValueError, TypeError):
            max_price = None

    # 2. Extract size (matches e.g. "size M", "size 29", "size Small", "size XXS")
    size = None
    size_match = re.search(r'\bsize\s+([a-zA-Z0-9/]+)\b', query, re.IGNORECASE)
    if size_match:
        size = size_match.group(1).upper()

    # 3. Clean up the query to extract description keywords
    cleaned = query
    if price_match:
        cleaned = cleaned.replace(price_match.group(0), "")
    if size_match:
        cleaned = cleaned.replace(size_match.group(0), "")

    # Strip conversational filler words and punctuation
    for filler in [",", "looking for", "find me", "a", "an", "the", "under", "with"]:
        cleaned = re.sub(rf'\b{re.escape(filler)}\b', '', cleaned, flags=re.IGNORECASE)

    description = " ".join(cleaned.replace(",", " ").split())
    return description, size, max_price


# ── session state ─────────────────────────────────────────────────────────────


def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.
    """
    if hasattr(trace, "start_trace"):
        trace.start_trace()

    session = new_session(query, wardrobe)

    iteration_count = 1
    if hasattr(trace, "check_iterations"):
        trace.check_iterations(iteration_count)

    # Step 1: Parse query
    desc, size, max_price = parse_query_params(query)
    session["parsed"] = {
        "description": desc,
        "size": size,
        "max_price": max_price,
    }
    if hasattr(trace, "step"):
        trace.step("parse_query", inputs={"query": query}, returned=session["parsed"])

    # Step 2: Call search_listings via MCP
    search_inputs = {"description": desc, "size": size, "max_price": max_price}
    results = call_tool("search_listings", search_inputs)
    session["search_results"] = results
    if hasattr(trace, "step"):
        trace.step("search_listings (via MCP)", inputs=search_inputs, returned=results)

    # Branch Rule
    if not results:
        details = []
        if desc:
            details.append(f"keywords '{desc}'")
        if size:
            details.append(f"size '{size}'")
        if max_price is not None:
            details.append(f"price under ${max_price:.2f}")

        criteria_str = ", ".join(details) if details else f"'{query}'"
        session["error"] = (
            f"No matching listings found matching {criteria_str}. "
            "Try increasing your budget, removing size filters, or broadening your keywords."
        )
        if hasattr(trace, "step"):
            trace.step("branch_decision", note="empty results -> stopping before model calls")
        return session

    # Step 3: Happy path — select first item
    session["selected_item"] = results[0]

    # Step 4: Call Tool 2 (suggest_outfit)
    try:
        outfit = suggest_outfit(
            new_item=session["selected_item"],
            wardrobe=session["wardrobe"]
        )
        session["outfit_suggestion"] = outfit
        if hasattr(trace, "step"):
            trace.step("suggest_outfit", inputs={"item": session["selected_item"].get("title")}, returned=outfit)
    except ModelUnavailable as e:
        session["error"] = f"Model service currently unavailable: {e}"
        if hasattr(trace, "step"):
            trace.step("suggest_outfit", note=f"failed: {e}")
        return session

    # Step 5: Call Tool 3 (create_fit_card)
    try:
        fit_card = create_fit_card(
            outfit=session["outfit_suggestion"],
            new_item=session["selected_item"]
        )
        session["fit_card"] = fit_card
        if hasattr(trace, "step"):
            trace.step("create_fit_card", inputs={"item": session["selected_item"].get("title")}, returned=fit_card)
    except ModelUnavailable as e:
        session["error"] = f"Model service currently unavailable: {e}"
        if hasattr(trace, "step"):
            trace.step("create_fit_card", note=f"failed: {e}")
        return session

    return session


# ── running it directly ───────────────────────────────────────────────────────


def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )