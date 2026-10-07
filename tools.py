"""
The three FitFindr tools.


Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.


    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str


All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.


⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re
import config  # noqa: F401 — you'll use this in search_listings
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.


    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.


    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".


                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.


    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.


    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform


    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.


    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.


    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    listings = load_listings()
    matches = []

    # Clean and extract query keywords (words >= 2 characters)
    keywords = [kw.lower() for kw in re.findall(r"\b\w+\b", description.lower()) if len(kw) >= 2]
    
    # Target size normalization (e.g. "M", "S/M", "US 9")
    norm_target_size = size.strip().lower() if size else None

    for item in listings:
        # 1. Price filter (item price <= max_price)
        if max_price is not None:
            try:
                if float(item.get("price", 0)) > float(max_price):
                    continue
            except (ValueError, TypeError):
                continue

        # 2. Size filter (safe exact/split match to prevent 's' in 'us 9' or 'l' in 'xl')
        if norm_target_size:
            raw_item_size = str(item.get("size", "")).strip().lower()
            # Split compound sizes like "S/M" or "M/L"
            item_size_tokens = [s.strip() for s in re.split(r"[/,\s]+", raw_item_size) if s.strip()]
            if norm_target_size != raw_item_size and norm_target_size not in item_size_tokens:
                continue

        # 3. Score keyword overlap across title, description, category, and style_tags
        title = item.get("title", "").lower()
        desc = item.get("description", "").lower()
        category = item.get("category", "").lower()
        tags = " ".join(item.get("style_tags", [])).lower()
        colors = " ".join(item.get("colors", [])).lower()
        full_text = f"{title} {desc} {category} {tags} {colors}"

        score = 0
        for kw in keywords:
            # Word boundary matching prevents substring false hits
            if re.search(rf"\b{re.escape(kw)}\b", full_text):
                # Extra weight for matches in title or style tags
                score += 2 if re.search(rf"\b{re.escape(kw)}\b", title) else 1

        # 4. Drop anything scoring zero (must match at least one keyword if keywords provided)
        if keywords and score == 0:
            continue

        matches.append((score, item))

    # 5. Sort by score descending and return listing dicts up to SEARCH_RESULT_LIMIT
    matches.sort(key=lambda x: x[0], reverse=True)
    limit = getattr(config, "SEARCH_RESULT_LIMIT", 5)
    return [item for _, item in matches[:limit]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.


    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.


    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.


    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.


    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.


    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    if not new_item:
        return "No item provided to style."

    item_title = new_item.get("title", "thrifted item")
    item_desc = new_item.get("description", "")
    item_color = ", ".join(new_item.get("colors", []))
    item_price = new_item.get("price", "N/A")

    wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []

    # 1. & 2. Empty wardrobe: ask for general styling advice
    if not wardrobe_items:
        prompt = f"""You are a personal stylist. The user is considering purchasing this item:
Item: {item_title} (${item_price})
Colors: {item_color}
Description: {item_desc}

The user has not provided an existing wardrobe. Provide 2 versatile, stylish outfit ideas and styling recommendations for how to wear this piece with everyday essentials."""
    # 3. Non-empty wardrobe: pair with specific owned pieces
    else:
        wardrobe_list_str = "\n".join(
            [f"- {w.get('name', w.get('title', 'Item'))} ({w.get('category', 'Clothing')}, {w.get('color', '')})" for w in wardrobe_items]
        )
        prompt = f"""You are a personal stylist. The user is considering purchasing this item:
Item: {item_title} (${item_price})
Colors: {item_color}
Description: {item_desc}

Here is the user's current wardrobe:
{wardrobe_list_str}

Suggest 1 or 2 specific outfit combinations by pairing this new item with specific pieces they already own from their wardrobe. Explain briefly why the combination works."""

    # 4. Return model response
    response = generate(prompt)
    return response.strip() if response else "Pair this item with neutral basics and classic sneakers."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.


    This calls the model too.


    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.


    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.


    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.


    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:


        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time


    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.


    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    # 1. Guard against empty or whitespace-only outfit
    if not outfit or not outfit.strip():
        return "Could not create fit card: outfit suggestions are missing."

    if not new_item:
        return "Could not create fit card: item details are missing."

    item_title = new_item.get("title", "thrift find")
    item_price = new_item.get("price", "N/A")
    item_platform = new_item.get("platform", "online thrift")

    # 2. Build prompt with item details and outfit pairing
    prompt = f"""You are writing a short, authentic social media caption (a Fit Card) for a thrift enthusiast sharing their new find.

Item: {item_title}
Price: ${item_price}
Platform: {item_platform}
Outfit Styling: {outfit}

Write a natural 2 to 4 sentence caption that:
- Reads like a real personal post (not an advertisement or product description).
- Mentions the item title, its price (${item_price}), and the platform ({item_platform}) exactly once.
- Conveys the vibe of the outfit and how it's styled.
- Includes 2-3 relevant hashtags."""

    # 3. Call generate() and return response
    response = generate(prompt)
    if response and response.strip():
        return response.strip()

    return f"Just thrifted this {item_title} for ${item_price} on {item_platform}! Styling it with my favorite wardrobe staples. #ThriftFinds #OOTD"