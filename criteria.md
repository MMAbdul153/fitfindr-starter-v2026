# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
My search uses keyword matching and regex parameter extraction, which can occasionally miss phrasing variations, and downstream LLM generation could occasionally fail on model timeouts or malformed JSON responses. 4 of 5 allows for realistic natural language variance while requiring high overall pipeline reliability.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
Stopping on an empty list is deterministic Python branching logic in the planning loop (`if not session["search_results"]`), not a probabilistic LLM decision. Since no model calls are involved in making this branch decision, it should never fail across 5 tries.

---

## 3. State integrity across tool boundaries

When `search_listings` returns matching items, the selected listing's `id`, `title`, `price`, and `platform` in `session["selected_item"]` match the exact values received by `suggest_outfit` and `create_fit_card` in 5 of 5 tries.

**Why this target:**
Passing data across tools happens entirely through dictionary updates in `session`. Because Python dictionary reads and writes are deterministic, there should be zero data corruption, dropped keys, or type mutations across tool boundaries in any run.

---

## 4. Grounded and distinctive fit card captions

In at least 4 of 5 successful runs, the generated fit card caption explicitly includes the selected item's price and references at least one named wardrobe item from the user's closet.

**Why this target:**
`create_fit_card` calls an LLM, so exact phrasing will vary. However, grounding rules in the prompt should consistently force the model to cite concrete facts (price and paired closet pieces) rather than generic fluff in at least 4 of 5 generations.

---

## 5. Strict price ceiling adherence

When the user query specifies a maximum price (e.g., 'under $30'), the selected item in `session["selected_item"]` has a `price` less than or equal to that ceiling in 5 of 5 matching runs.

**Why this target:**
Price filtering is executed in Python within `search_listings` via `float(item["price"]) <= max_price`. Because numeric comparison in code is exact and deterministic, the agent should never select or style an item that violates the user's stated budget constraint.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->