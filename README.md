# ai-agents-battle

## Requirements

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) for environments and dependencies

## Setup

```bash
uv sync
```

This creates `.venv` and installs everything from `pyproject.toml`. Use this interpreter in your editor (or rely on `uv run`, which uses it automatically).

## Run

One process controls one tank. Use a distinct name per terminal if you want multiple bots in the same lobby.

```bash
uv run python main.py
```

Default name is `Matrix`, or set `TANK_NAME` in the environment / `.env`:

```bash
TANK_NAME=Trinity uv run python main.py
```

Override per run:

```bash
uv run python main.py --name Neo
```

### Allies (your own tanks won’t team-kill)

If you run **multiple** bots and want them to **ignore guaranteed killshots on each other** until every **non-ally** tank is gone, pass the **same comma-separated list** on every process (include **all** of your tank names).

```bash
ALLY_TANK_NAMES=Matrix,Neo,Morpheus uv run python main.py --name Matrix
```

```bash
uv run python main.py --name Neo --allies Matrix,Neo,Morpheus
```

While **any** enemy **not** in that list is alive, shots on allies are dropped; **focus**, **threat**, and **next-player** penalties treat allies more softly so you don’t only dance away from each other. When **only** allies remain, behavior is unchanged—they **can** shoot each other.

