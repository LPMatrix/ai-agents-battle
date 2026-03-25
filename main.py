import json
import time
from client import MCPClient
from context import GameContext
from state import ValidActions
from strategy import decide

TANK_NAME = "Matrix"

client = MCPClient()

def parse(response):
    return json.loads(response["content"][0]["text"])

def play_turn(game_state: dict | None):
    raw = client.get_valid_actions()
    data = parse(raw)
    valid_actions = ValidActions(data)
    ctx = GameContext.from_game_state(game_state, TANK_NAME) if game_state else None
    actions = decide(valid_actions, ctx)

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


def game_loop():
    print("Registering Matrix...")
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
            (id for id, t in state["tanks"].items() if t["name"] == TANK_NAME),
            None
        )

        if current_turn == my_id:
            print("My turn — deciding...")
            play_turn(state)
        else:
            time.sleep(1)

if __name__ == "__main__":
    game_loop()
