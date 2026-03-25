# LinkedIn article draft — Tank arena bot & MCP (living document)

> **How to use this file:** Copy sections into LinkedIn’s article editor. LinkedIn handles headings and bold poorly from Markdown—apply formatting in the UI. Update the **Revision log** at the bottom when you change the narrative.

---

## Suggested headline (pick one)

1. **I built a Python bot for a tank battle game—and learned more about HTTP than I expected**
2. **What a weekend project taught me about MCP, `uv`, and honest game AI**
3. **From “call an API” to “speak MCP”: shipping a small autonomous player**
4. **Heuristics over hype: what a tank bot taught me about real “agent” loops**
5. **Multiplayer FFA on the wire: teaching a Python bot to care about turn order**

---

## Draft body

**The hook**

Most “AI agent” demos stop at a chat box. I wanted something messier: a real loop—read state, decide, act—against a live game server. So I wired up a small Python client for a tank arena-style game and gave it a hand-written strategy. The game part is fun; the engineering lessons stuck with me.

**What I shipped**

A **Python 3.13** project managed with **`uv`**: `uv sync`, then `uv run python main.py`—no local package install, no `egg-info` clutter; just dependencies and scripts.

The client talks to the game over **MCP (Model Context Protocol)** with **Streamable HTTP**: **`initialize`**, session headers, then tool calls like `get_valid_actions`, `rotate`, `move`, and `fire`. Under the hood that’s **`httpx`** and the same **`Accept: application/json, text/event-stream`** negotiation a spec-compliant MCP client uses—not a one-off REST guess.

The codebase split into thin layers: **`client.py`** (protocol + JSON-RPC), **`state.py`** (parse payloads into small objects), **`geometry.py`** (grid / directions), **`context.py`** (a **`GameContext`** slice of full game state), **`strategy.py`** (what to do this turn), and **`main.py`** (lobby loop, **`play_turn(state)`** so the brain sees both **`get_valid_actions`** and **standings / turn order**).

**The “brain” (on purpose, not magic)**

Still **no LLM in the hot path**—only geometry, heuristics, and whatever the server marks legal.

The multiplayer pass made that honest: **`get_valid_actions`** is still the authority for **guaranteed hits**, but **which** kills to take first now depends on **focus fire** (finish weak tanks vs **pressure the score leader** when I’m behind), and **two simultaneous killshots** are chosen with **distinct dice** and a simple priority score—not whatever order the JSON happened to list.

**Threat** uses **`lastRoll`** when the API provides it (otherwise a 1–6 fallback along facing). **Defense** got a taste of **tempo**: when **`turnOrder`** is available, I **penalize landing on cells** the **next player** could hit from their **current** barrel line—rough, but it’s the difference between 1v1 intuition and “three people at the table.”

If a turn would otherwise be empty, the bot falls back to a **legal rotate** toward the current focus target—small UX win against “stuck” sub-phases.

Iterating also surfaced API shape: **`die1` / `die2` can be `null`**, **`me` / `you`** for the player blob, and **second moves** must be planned from the **cell after the first** (try **(1→2)** and **(2→1)** when only one die is active first).

**What actually slowed me down (and why that’s useful)**

1. **406 Not Acceptable** — The endpoint wasn’t broken; my client was. MCP Streamable HTTP expects the right **`Accept`** (and friends). Lesson: read the **transport**, not only the JSON body.

2. **Notebooks vs async** — In Jupyter, MCP’s AnyIO usage and the kernel’s event loop fought each other (`CancelledError` during `initialize`). Running MCP work in a **separate thread with its own event loop** fixed exploration. Lesson: notebooks and production-shaped async aren’t always the same animal.

3. **The server is the source of truth** — **`null` dice**, **`you` vs `me`** for the player blob across payload versions, tool results nested under MCP **`content`**: defensive parsing at the boundary beats **`KeyError`** and **`TypeError`** deep inside “strategy.” If your bot crashes mid-match, assume the schema first—not your heuristics.

4. **Packaging vs how you run** — A setuptools **`package = true`** install gave me console scripts—and a **`*.egg-info`** directory I didn’t need. For this repo, **dependencies-only `uv`** is enough. Match tooling to how you actually ship and run.

5. **Types and runtimes** — Pinning **Python 3.13** in **`pyproject.toml`** and using **`uv run`** avoids “works on my laptop” with an old system Python where even type syntax can fail at import time.

**Why I’m sharing this**

Small projects are a low-risk place to touch **protocols**, **async**, and **agent-shaped loops** without claiming general intelligence. If you’re growing in backend or integration work, a client that follows a spec plus a bot that respects game rules is honest practice—and a better story than another wrapper around a chat API.

**What’s next (optional — edit as you go)**

- **Deeper opponent modeling** (simulate the next player’s rotate/move, not only their current line-of-fire).
- A/B **hand-tuned strategy** vs an **LLM planner** that only chooses *intent* while code enumerates legal actions.
- Publish the **repo** and drop the link here when you’re ready.

---

## Short version (LinkedIn post if you prefer not to use Articles)

Shipped a **Python 3.13** **multiplayer** tank bot: **MCP Streamable HTTP**, **`uv`**, **`httpx`**, plus a **`GameContext`** from **`get_game_state`** so **`decide()`** sees **turn order** and **scores**. Heuristics: **ranked killshots**, **focus fire** (weakest vs **leader** when behind), **`lastRoll`-aware** threats, a **next-player** landing penalty, and **rotate** if nothing else applies. Same hard lessons as before—**406** / **`Accept`**, **Jupyter + MCP** isolation, **`null` dice** and **`me`/`you`**—**parse at the boundary**. **`uv run python main.py`** only; no local package noise.

---

## Revision log

| Date        | Change |
|------------|--------|
| *(initial)* | First draft: MCP, uv, 406, notebooks, packaging. |
| 2026-03-23 | Synced with repo: module layout, nullable dice + two-die ordering, `me`/`you` normalization, no local package install, Python 3.13 / `uv run`, expanded lessons and short post. |
| 2026-03-24 | Multiplayer strategy: `context.py` / `GameContext`, ranked killshots + distinct dice, focus vs leader when behind, `lastRoll` threats, next-player landing penalty, rotate fallback; `play_turn(state)` wiring; “what’s next” trimmed. |

---

## Checklist before you publish

- [ ] Replace generic phrases with **your** goal (learning, portfolio, team hackathon, etc.).
- [ ] Add **one screenshot** or diagram if LinkedIn allows (game state, architecture sketch).
- [ ] Link **repo** or say “DM for code” if private.
- [ ] Remove any claim you can’t defend (win rate, latency, production use).
- [ ] Run a quick **grammar pass** in the LinkedIn editor (their preview is truth).
