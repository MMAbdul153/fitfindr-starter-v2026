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
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


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

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. Check session["error"] first — if it isn't None,
        the run ended early and the later fields will still be None.
    """
    # 1. Start session
    session = new_session(query, wardrobe)

    # 2. Check iteration bounds
    iteration_count = 1
    if hasattr(trace, "check_iterations"):
        trace.check_iterations(iteration_count)

    # 3. Step 1: Parse query into description, size, and max_price
    desc, size, max_price = parse_query_params(query)
    session["parsed"] = {
        "description": desc,
        "size": size,
        "max_price": max_price,
    }

    # 4. Step 2: Call Tool 1 (search_listings)
    results = search_listings(description=desc, size=size, max_price=max_price)
    session["search_results"] = results

    # ⚠️ THIS IS THE BRANCH: If nothing came back, halt execution immediately
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
        return session

    # 5. Step 3: Happy path — choose the first result
    session["selected_item"] = results[0]

    # 6. Step 4: Call Tool 2 (suggest_outfit)
    try:
        outfit = suggest_outfit(
            new_item=session["selected_item"],
            wardrobe=session["wardrobe"]
        )
        session["outfit_suggestion"] = outfit
    except ModelUnavailable as e:
        session["error"] = f"Model service currently unavailable: {e}"
        return session

    # 7. Step 5: Call Tool 3 (create_fit_card)
    try:
        fit_card = create_fit_card(
            outfit=session["outfit_suggestion"],
            new_item=session["selected_item"]
        )
        session["fit_card"] = fit_card
    except ModelUnavailable as e:
        session["error"] = f"Model service currently unavailable: {e}"
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