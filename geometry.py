DIRECTIONS = {
    "N":  (0, -1),
    "NE": (1, -1),
    "E":  (1,  0),
    "SE": (1,  1),
    "S":  (0,  1),
    "SW": (-1, 1),
    "W":  (-1, 0),
    "NW": (-1,-1),
}

def step(x, y, direction, distance):
    dx, dy = DIRECTIONS[direction]
    return x + dx * distance, y + dy * distance

def direction_and_distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    for name, (ddx, ddy) in DIRECTIONS.items():
        if dx * ddy != dy * ddx:
            continue
        if ddx != 0:
            t = dx // ddx
        elif ddy != 0:
            t = dy // ddy
        else:
            continue
        if t > 0 and dx == t * ddx and dy == t * ddy:
            return name, t
    return None, None

def is_threatened(x, y, enemies):
    for enemy in enemies:
        ex, ey = enemy["x"], enemy["y"]
        last_roll = enemy.get("lastRoll")
        if last_roll is not None:
            dice_values = [last_roll]
        else:
            # no roll yet — enemy has no active shot, not a ranged threat
            dice_values = []
        for die_val in dice_values:
            for direction in DIRECTIONS:
                lx, ly = step(ex, ey, direction, die_val)
                if lx == x and ly == y:
                    return True
    return False