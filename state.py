class Tank:
    def __init__(self, data):
        self.x = data["x"]
        self.y = data["y"]
        self.direction = data["direction"]
        self.score = data["score"]

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

class ValidActions:
    def __init__(self, data):
        self.grid_size = data["gridSize"]
        self.me = Me(data["you"])
        self.enemies = [Tank({**e, "score": e.get("score", 5)}) for e in data["enemies"]]
        self.valid_rotations = data["validRotations"]
        self.die1 = Die(data["die1"])
        self.die2 = Die(data["die2"])

    def killshots(self):
        shots = []
        for die in (d for d in (self.die1, self.die2) if d is not None):
            for shot in die.valid_shots:
                if shot["target"] is not None:
                    shots.append({"die": die.index, "direction": shot["direction"], "target": shot["target"]})
        return shots