from geometry import step, direction_and_distance, DIRECTIONS

def decide(valid_actions):
    killshots = valid_actions.killshots()
    me = valid_actions.me
    enemies = valid_actions.enemies
    threatened_by = _who_threatens_me(me, enemies)
    actions = []

    if len(killshots) >= 2:
        for shot in killshots[:2]:
            actions.append({"action": "fire", "die": shot["die"], "direction": shot["direction"]})
        return actions

    if len(killshots) == 1:
        shot = killshots[0]
        threat = threatened_by[0] if threatened_by else None

        actions.append({"action": "fire", "die": shot["die"], "direction": shot["direction"]})
        remaining_die = 2 if shot["die"] == 1 else 1

        if threat and threat.name != shot["target"]:
            flee = _best_escape(me, enemies, valid_actions, remaining_die)
            if flee:
                actions.append(flee)
        else:
            reposition = _best_reposition(me, enemies, valid_actions, remaining_die)
            if reposition:
                actions.append(reposition)
        return actions

    if threatened_by:
        escape1 = _best_escape(me, enemies, valid_actions, 1)
        if escape1:
            actions.append(escape1)
            new_x, new_y = step(me.x, me.y, escape1["direction"], valid_actions.die1.value)
            escape2 = _best_escape_from(new_x, new_y, enemies, valid_actions, 2)
            if escape2:
                actions.append(escape2)
        return actions

    reposition1 = _best_reposition(me, enemies, valid_actions, 1)
    if reposition1:
        actions.append(reposition1)
        new_x, new_y = step(me.x, me.y, reposition1["direction"], valid_actions.die1.value)
        reposition2 = _best_reposition_from(new_x, new_y, enemies, valid_actions, 2)
        if reposition2:
            actions.append(reposition2)
    return actions


def _who_threatens_me(me, enemies):
    threatened_by = []
    for enemy in enemies:
        dx, dy = DIRECTIONS[enemy.direction]
        for dist in range(1, 7):
            lx = enemy.x + dx * dist
            ly = enemy.y + dy * dist
            if lx == me.x and ly == me.y:
                threatened_by.append(enemy)
                break
    return threatened_by


def _best_escape(me, enemies, valid_actions, die_index):
    return _best_escape_from(me.x, me.y, enemies, valid_actions, die_index)


def _best_escape_from(x, y, enemies, valid_actions, die_index):
    die = valid_actions.die1 if die_index == 1 else valid_actions.die2
    enemy_positions = {(e.x, e.y) for e in enemies}
    best_dir = None
    best_score = -1

    for direction in die.valid_moves:
        nx, ny = step(x, y, direction, die.value)
        if (nx, ny) in enemy_positions:
            continue
        score = _safety_score(nx, ny, enemies)
        if score > best_score:
            best_score = score
            best_dir = direction

    if best_dir:
        return {"action": "move", "die": die_index, "direction": best_dir}
    return None


def _best_reposition(me, enemies, valid_actions, die_index):
    return _best_reposition_from(me.x, me.y, enemies, valid_actions, die_index)


def _best_reposition_from(x, y, enemies, valid_actions, die_index):
    die = valid_actions.die1 if die_index == 1 else valid_actions.die2
    enemy_positions = {(e.x, e.y) for e in enemies}
    best_dir = None
    best_score = -1

    for direction in die.valid_moves:
        nx, ny = step(x, y, direction, die.value)
        if (nx, ny) in enemy_positions:
            continue
        score = _offensive_score(nx, ny, enemies, die.value)
        if score > best_score:
            best_score = score
            best_dir = direction

    if best_dir:
        return {"action": "move", "die": die_index, "direction": best_dir}
    return None


def _safety_score(x, y, enemies):
    total = 0
    for enemy in enemies:
        dx = abs(x - enemy.x)
        dy = abs(y - enemy.y)
        total += max(dx, dy)
    return total


def _offensive_score(x, y, enemies, die_value):
    score = 0
    for enemy in enemies:
        _, dist = direction_and_distance(x, y, enemy.x, enemy.y)
        if dist is not None and dist == die_value:
            score += 10
        elif dist is not None:
            score += 1
    return score