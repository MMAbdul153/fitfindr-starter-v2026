# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr is an AI-powered personal shopping and styling assistant. A user provides a natural language query describing a desired thrift piece (including optional budget and size constraints), and the system searches available second-hand listings in real-time. If matching items are found, the agent pairs the selected item with complementary pieces from the user's existing wardrobe and generates a styled social-media caption (Fit Card). If no listings match, the agent halts early with a helpful refusal message before making downstream model calls.

---

## Tool Inventory

### `search_listings`

- **What it does:** Searches the listings dataset for items matching description keywords, optional size, and optional maximum price limit.
- **Inputs:** `description` (str), `size` (str | None), `max_price` (float | None)
- **Returns:** A list of dicts, each with keys `id` (str), `title` (str), `price` (float), `size` (str), `platform` (str), `description` (str), `category` (str), `style_tags` (list[str]), `condition` (str), `colors` (list[str]), and `brand` (str | None).
- **When it has nothing:** Returns an empty list `[]`.

### `suggest_outfit`

- **What it does:** Calls the model to select complementary pieces from the user's wardrobe to pair with the newly selected listing.
- **Inputs:** `new_item` (dict with item attributes), `wardrobe` (dict representing user wardrobe categories from `wardrobe_schema.json`)
- **Returns:** A styled text recommendation string (or dict) containing the selected complementary wardrobe items and an explanation of why the pairing works.
- **When it has nothing:** Returns an empty fallback string `""` (or `{}`) if `new_item` is empty or invalid.

### `create_fit_card`

- **What it does:** Calls the model to generate a concise, styled social caption highlighting the paired outfit with relevant hashtags.
- **Inputs:** `outfit` (dict | str representing the styled outfit), `new_item` (dict of the selected listing)
- **Returns:** A string containing the social-media-ready caption and hashtags.
- **When it has nothing:** Returns an empty string `""` if input data is missing.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, put an informative refusal message in `session["error"]` explaining what criteria failed and stop. Otherwise, assign the first result (`session["search_results"][0]`) to `session["selected_item"]` and proceed to `suggest_outfit` followed by `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex pattern matching in `agent.py::parse_query_params` to extract price thresholds (e.g. `under $30`) and size tags (e.g. `size M`), combined with string splitting/cleaning for description keywords.

**What moves through the session:** 
1. `session["query"]` (input string)
2. `session["parsed"]` (dict with `description`, `size`, `max_price`)
3. `session["search_results"]` (list of matched listing dicts from `search_listings`)
4. `session["selected_item"]` (chosen listing dict)
5. `session["wardrobe"]` (user wardrobe dict)
6. `session["outfit_suggestion"]` (output from `suggest_outfit`)
7. `session["fit_card"]` (final caption string from `create_fit_card`)
8. `session["error"]` (refusal message string if stopped early)

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'
=== Searching Listings ===
Query: 'vintage graphic tee', Max Price: $30.0
Found 6 matching items.
Selected item: Graphic Tee — 2003 Tour Bootleg Style ($24.0 on depop)

=== Generating Outfit Suggestion ===
Selected wardrobe pieces:
* White ribbed tank top (layering)
* Vintage black denim jacket
* Chunky white sneakers
* Black crossbody bag

Styling Note: The vintage bootleg graphic tee pairs effortlessly with an open black denim jacket and chunky sneakers for an authentic early-2000s streetwear look.

=== Fit Card ===
Scored this Graphic Tee — 2003 Tour Bootleg Style for just $24.0 on depop! Layered it over a white ribbed tank and styled with my vintage black denim jacket and chunky white sneakers. #VintageStreetwear #ThriftFinds #OOTD
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Hello! As your personal stylist, I am thrilled you're eyeing these vintage Levi's 501s. At $38, they are an absolute steal and a timeless wardrobe foundation. 

Since you already own some great slouchy bottoms (dark wash jeans and khaki trousers), these 501s will fill a crucial gap by giving you a classic, straight-leg fit with that coveted broken-in vintage texture. 

Here are two distinct outfit combinations using pieces straight from your closet:

### Look 1: Effortless Casual (Streetwear Vibe)
* **Top:** White ribbed tank top
* **Outerwear:** Vintage black denim jacket
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag

**Why it works:** 
This is the ultimate off-duty uniform. The fitted white ribbed tank creates a great silhouette against the straight-leg structure of the 501s. Layering your vintage black denim jacket on top creates a cool "denim-on-denim" moment (black and medium blue wash contrast each other beautifully), while the chunky white sneakers and black crossbody keep the look modern, sporty, and fresh. 

### Look 2: Elevated Grunge (Cool & Cozy)
* **Top:** Black cropped zip hoodie
* **Shoes:** Black combat boots
* **Accessories:** Brown leather belt

**Why it works:**
Tuck the front of the 501s in slightly to showcase the brown leather belt, which adds a nice touch of warmth against the cool medium-wash denim. Pairing the jeans with your black combat boots gives you that classic 90s rock-and-roll edge. Finishing with the black cropped zip hoodie balances the relaxed fit of the jeans with a sharp, cropped top line, making the whole outfit look intentional and effortlessly cool.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these Vintage Levi's 501 Jeans — Medium Wash on depop for just $38.0 and I am honestly never taking them off. They have that 100% broken-in denim feel that you just can't buy new. Paired them with crisp white sneakers for that classic, effortless Sunday look. #thriftedstyle #vintagelevis #depopfinds
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* How to ensure `search_listings` handles empty results safely so the planning loop in `agent.py` can make a clean refusal branch without crashing downstream.
- *What came back:* Claude recommended returning an explicit empty list `[]` instead of `None` or raising an exception, and checking `if not session["search_results"]:` as the first deterministic branch condition.
- *What I changed:* I adopted the explicit empty list `[]` return pattern in `tools.py` and implemented the early refusal return in `agent.py::run_agent`, setting a helpful error message and leaving `session["fit_card"] = None`.

**Moment 2**

- *What I asked for:* A robust regex query parser in `agent.py` to extract budget ceilings (e.g. `under $30`, `< $50`) and size identifiers (e.g. `size M`, `size 29`) from natural language queries.
- *What came back:* Claude provided regex patterns `(?:under|<|\$)\s*(\d+(?:\.\d+)?)` and `size\s+([a-zA-Z0-9/]+)`, along with string-cleaning logic to strip filler phrases.
- *What I changed:* I incorporated this parser into `agent.py::parse_query_params` to reliably populate `session["parsed"]` before invoking `search_listings`.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. State integrity across tool boundaries | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Grounded and distinctive fit card captions | 4 of 5 | PASS | FAIL | PASS | PASS | FAIL | MISSED (3/5) |
| 5. Strict price ceiling adherence | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```
# Output from scenarios.py::run_scenario_4 (Try 2 - FAILED Grounding Check)
# File & function: agent.py::run_agent -> tools.py::create_fit_card

Query: "vintage graphic tee under $30"
Selected Item: Graphic Tee — 2003 Tour Bootleg Style ($24.0 on depop)
Wardrobe Context: {"tops": ["White ribbed tank top", "Black cropped zip hoodie"], "outerwear": ["Vintage black denim jacket"]}

Fit Card Output:
"Obsessed with this vintage graphic tee! Such an effortless thrifted aesthetic that pairs with literally anything in your closet. #OOTD #VintageStyle"

Scorer Verdict: FAIL
Reason: The generated caption omitted the item's explicit price ($24.0) and did not name any specific piece from the retrieved wardrobe (e.g., 'Vintage black denim jacket').
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | MET | Passed 5 of 5 tries across all standard search scenarios. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET | Passed 5 of 5 tries, cleanly stopping at the empty search branch with 0 model calls. |
| 3 | State integrity across tool boundaries | 5 of 5 | MET | Passed 5 of 5 tries; dictionary keys and types in session['selected_item'] remained perfectly intact. |
| 4 | Grounded and distinctive fit card captions | 4 of 5 | MISSED | Passed only 3 of 5 tries (Try 2 and Try 5 omitted explicit price figures and specific closet item names). |
| 5 | Strict price ceiling adherence | 5 of 5 | MET | Passed 5 of 5 tries; all selected items had listing prices strictly <= user max_price. |
**Diagnoses**

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace
 parse_query
 in: {'query': 'vintage graphic tee under $30'}
 out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
 search_listings (via MCP)
 in: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
 out: [{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'price': 24.0, ...}, ...] (6 items)
 suggest_outfit
 in: {'item': 'Graphic Tee — 2003 Tour Bootleg Style'}
 out: Look 1: Effortless Casual (Streetwear Vibe)...
 create_fit_card
 in: {'item': 'Graphic Tee — 2003 Tour Bootleg Style'}
 out: Scored this Graphic Tee — 2003 Tour Bootleg Style for $24.0 on depop! Styled with my vintage black denim jacket. #OOTD #ThriftFinds
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
 parse_query
 in: {'query': 'designer ballgown size XXS under $5'}
 out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
 search_listings (via MCP)
 in: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
 out: [] (0 items)
 branch_decision
 → empty results -> stopping before model calls
```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->
```
`search_listings` was wrapped as a registered MCP tool inside `mcp_server.py` and called using `mcp_client.call_tool`. The tool outputs and return signatures remained identical to the direct Python call, ensuring zero pipeline regressions while isolating the tool interface over stdio
```


---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
