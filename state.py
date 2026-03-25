class Tank:
    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name", "")
        self.x = data["x"]
        self.y = data["y"]
        self.direction = data["direction"]
        self.score = data["score"]
        # If set, threat model uses this range only; else 1–6.
        self.last_roll = data.get("lastRoll")

class Me(Tank):
    def __init__(self, data):
        super().__init__(data)
        self.dice = data["dice"]
        self.used_dice = data["usedDice"]

class Die:
    def __init__(self, data):
        self.index = data["die"]
        self.value = data["value"]
        self.valid_moves = data["validMoves"]
        self.valid_shots = data["validShots"]

def _player_blob(data: dict) -> dict:
    blob = data.get("me")
    if blob is not None:
        return blob
    blob = data.get("you")
    if blob is not None:
        return blob
    raise KeyError("valid actions must include 'me' or 'you'")


class ValidActions:
    def __init__(self, data):
        self.grid_size = data["gridSize"]
        self.me = Me(_player_blob(data))
        self.enemies = [Tank({**e, "score": e.get("score", 5)}) for e in data["enemies"]]
        self.valid_rotations = data["validRotations"]
        # API sends null when that die is not actionable this sub-phase.
        self.die1 = Die(data["die1"]) if data.get("die1") is not None else None
        self.die2 = Die(data["die2"]) if data.get("die2") is not None else None

    def killshots(self):
        shots = []
        for die in (d for d in (self.die1, self.die2) if d is not None):
            for shot in die.valid_shots:
                if shot["target"] is not None:
                    shots.append({"die": die.index, "direction": shot["direction"], "target": shot["target"]})
        return shots