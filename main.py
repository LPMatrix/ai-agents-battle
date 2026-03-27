import argparse
import json
import os
import sys
import time

from dotenv import load_dotenv

from client import MCPClient
from context import GameContext
from state import ValidActions
from strategy import decide

DEFAULT_TANK_NAME = "Matrix"


def parse(response):
    return json.loads(response["content"][0]["text"])


def play_turn(
    client: MCPClient,
    tank_name: str,
    game_state: dict | None,
    ally_names: frozenset[str],
):
    raw = client.get_valid_actions()
    data = parse(raw)
    valid_actions = ValidActions(data)
    ctx = GameContext.from_game_state(game_state, tank_name) if game_state else None
    actions = decide(valid_actions, ctx, ally_names)

    for action in actions:
        if action["action"] == "fire":
            print(f"Firing die {action['die']} → {action['direction']}")
            client.rotate(action["direction"])
            client.fire(action["die"])
        elif action["action"] == "move":
            print(f"Moving die {action['die']} → {action['direction']}")
            client.rotate(action["direction"])
            client.move(action["die"])
        elif action["action"] == "rotate":
            print(f"Rotating → {action['direction']}")
            client.rotate(action["direction"])


def game_loop(client: MCPClient, tank_name: str, ally_names: frozenset[str]):
    print(f"Registering {tank_name!r}...")
    if ally_names:
        others = ", ".join(sorted(ally_names))
        print(f"Alliance: will not shoot {{{others}}} while non-allies remain.")
    client.register()

    while True:
        state = parse(client.get_game_state())

        if state["status"] == "lobby":
            print("Waiting for game to start...")
            time.sleep(3)
            continue

        if state["status"] == "ended":
            print("Game over.")
            break

        current_turn = state["currentTurnId"]
        my_id = next(
            (id for id, t in state["tanks"].items() if t["name"] == tank_name),
            None,
        )

        if current_turn == my_id:
            print("My turn — deciding...")
            play_turn(client, tank_name, state, ally_names)
        else:
            time.sleep(1)


def _resolve_tank_name(args: argparse.Namespace) -> str:
    if args.name is not None:
        return args.name.strip()
    return os.environ.get("TANK_NAME", DEFAULT_TANK_NAME).strip()


def _parse_ally_names(cli_value: str | None) -> frozenset[str]:
    raw = (
        cli_value
        if cli_value is not None
        else os.environ.get("ALLY_TANK_NAMES", "")
    ).strip()
    if not raw:
        return frozenset()
    return frozenset(p.strip() for p in raw.split(",") if p.strip())


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Battle tank bot (one process = one tank).",
    )
    parser.add_argument(
        "--name",
        metavar="TANK",
        default=None,
        help=f"tank name (default: env TANK_NAME or {DEFAULT_TANK_NAME!r})",
    )
    parser.add_argument(
        "--allies",
        metavar="NAMES",
        default=None,
        help=(
            "comma-separated ally names; no guaranteed shots on them while any "
            "non-ally tank remains (default: env ALLY_TANK_NAMES)"
        ),
    )
    args = parser.parse_args()
    tank_name = _resolve_tank_name(args)
    if not tank_name:
        print("Tank name must be non-empty.", file=sys.stderr)
        sys.exit(1)
    ally_names = _parse_ally_names(args.allies)

    with MCPClient(tank_name) as client:
        game_loop(client, tank_name, ally_names)


if __name__ == "__main__":
    main()
