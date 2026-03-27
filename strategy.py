"""Turn decision: multiplayer-aware heuristics (focus fire, turn order, threats)."""

from __future__ import annotations

from typing import Any

from geometry import DIRECTIONS, direction_and_distance, step


def _ally_name(enemy: Any) -> str:
    return (getattr(enemy, "name", None) or "").strip()


def _is_ally(enemy: Any, allies: frozenset[str]) -> bool:
    if not allies:
        return False
    return _ally_name(enemy) in allies


def _has_outsiders(enemies: list[Any], allies: frozenset[str]) -> bool:
    """True if some live enemy is not in the ally name set (pact only applies when this holds)."""
    if not enemies:
        return False
    if not allies:
        return True
    return any(not _is_ally(e, allies) for e in enemies)


def _filter_killshots_for_alliance(
    killshots: list[dict[str, Any]],
    enemies: list[Any],
    allies: frozenset[str],
) -> list[dict[str, Any]]:
    """Drop guaranteed hits on allies while any non-ally is still in the match."""
    if not allies or not _has_outsiders(enemies, allies):
        return killshots
    out: list[dict[str, Any]] = []
    for s in killshots:
        victim = _enemy_for_target(enemies, s["target"])
        if victim is not None and _is_ally(victim, allies):
            continue
        out.append(s)
    return out


def _same_tank(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return False
    if a is b:
        return True
    if getattr(a, "id", None) and getattr(b, "id", None) and a.id == b.id:
        return True
    if getattr(a, "name", None) and getattr(b, "name", None) and a.name == b.name:
        return True
    return False


def _enemy_for_target(enemies: list[Any], target: Any) -> Any | None:
    if target is None:
        return None
    for e in enemies:
        if getattr(e, "id", None) is not None and target == e.id:
            return e
        if getattr(e, "name", None) and target == e.name:
            return e
    return None


def _threat_matches_target(threat: Any, target: Any) -> bool:
    """True if the killshot target is the same tank as ``threat``."""
    if target is None:
        return False
    if getattr(threat, "id", None) is not None and target == threat.id:
        return True
    if getattr(threat, "name", None) and target == threat.name:
        return True
    return False


def _threat_distances(enemy: Any) -> list[int]:
    lr = getattr(enemy, "last_roll", None)
    if lr is not None and isinstance(lr, int) and lr > 0:
        return [lr]
    return list(range(1, 7))


def _who_threatens_me(
    me: Any, enemies: list[Any], allies: frozenset[str] | None = None
) -> list[Any]:
    threatened_by: list[Any] = []
    a = allies or frozenset()
    for enemy in enemies:
        dx, dy = DIRECTIONS[enemy.direction]
        for dist in _threat_distances(enemy):
            lx = enemy.x + dx * dist
            ly = enemy.y + dy * dist
            if lx == me.x and ly == me.y:
                threatened_by.append(enemy)
                break
    if a and _has_outsiders(enemies, a):
        threatened_by = [t for t in threatened_by if not _is_ally(t, a)]
    return threatened_by


def _incoming_from_tank_at(shooter: Any, tx: int, ty: int) -> int:
    """Penalty if ``shooter`` can hit cell (tx, ty) along current facing."""
    dx, dy = DIRECTIONS[shooter.direction]
    for dist in _threat_distances(shooter):
        if shooter.x + dx * dist == tx and shooter.y + dy * dist == ty:
            return 70
    return 0


def _next_opponent_tank(enemies: list[Any], game_ctx: Any | None) -> Any | None:
    if game_ctx is None:
        return None
    nid = game_ctx.next_player_id_after_me()
    if not nid:
        return None
    for e in enemies:
        if getattr(e, "id", None) == nid:
            return e
    return None


def _killshot_priority(
    shot: dict[str, Any],
    enemies: list[Any],
    threatened_ids: set[int],
    game_ctx: Any | None,
) -> float:
    e = _enemy_for_target(enemies, shot["target"])
    if e is None:
        return -10_000.0
    p = float((6 - e.score) * 25)
    if game_ctx is not None and game_ctx.i_am_behind_leader():
        p += float(e.score * 8)
    if id(e) in threatened_ids:
        p += 18.0
    return p


def _pick_killshots(
    killshots: list[dict[str, Any]],
    enemies: list[Any],
    threatened_by: list[Any],
    game_ctx: Any | None,
) -> list[dict[str, Any]]:
    """Up to two shots with distinct dice, ranked for focus fire / standings."""
    tb_ids = {id(t) for t in threatened_by}
    pri = lambda s: _killshot_priority(s, enemies, tb_ids, game_ctx)
    ordered = sorted(killshots, key=pri, reverse=True)
    picked: list[dict[str, Any]] = []
    used_dice: set[int] = set()
    for s in ordered:
        d = s["die"]
        if d in used_dice:
            continue
        picked.append(s)
        used_dice.add(d)
        if len(picked) >= 2:
            break
    return picked


def _focus_target(
    me: Any,
    enemies: list[Any],
    game_ctx: Any | None,
    allies: frozenset[str],
) -> Any | None:
    if not enemies:
        return None
    pool = list(enemies)
    if allies and _has_outsiders(enemies, allies):
        pool = [e for e in enemies if not _is_ally(e, allies)]
    if not pool:
        pool = list(enemies)
    if game_ctx is not None and game_ctx.i_am_behind_leader():
        return max(pool, key=lambda e: e.score)
    return min(pool, key=lambda e: e.score)


def _finalize(
    actions: list[dict[str, Any] | None],
    valid_actions: Any,
    me: Any,
    enemies: list[Any],
    game_ctx: Any | None,
    allies: frozenset[str],
) -> list[dict[str, Any]]:
    out = [a for a in actions if a]
    if out:
        return out
    focus = _focus_target(me, enemies, game_ctx, allies)
    rot = _fallback_rotate(valid_actions, me, focus)
    return [rot] if rot else []


def _fallback_rotate(valid_actions: Any, me: Any, focus: Any | None) -> dict[str, Any] | None:
    rotations = getattr(valid_actions, "valid_rotations", None) or []
    if not rotations:
        return None
    if focus is None:
        return {"action": "rotate", "direction": rotations[0]}
    best_dir = None
    best_dist = 10**9
    for d in rotations:
        nx, ny = step(me.x, me.y, d, 1)
        dist = max(abs(nx - focus.x), abs(ny - focus.y))
        if dist < best_dist:
            best_dist = dist
            best_dir = d
    return {"action": "rotate", "direction": best_dir} if best_dir else None


def decide(
    valid_actions: Any,
    game_ctx: Any | None = None,
    ally_names: frozenset[str] | None = None,
) -> list[dict[str, Any]]:
    allies = ally_names or frozenset()
    killshots = _filter_killshots_for_alliance(
        valid_actions.killshots(), valid_actions.enemies, allies
    )
    me = valid_actions.me
    enemies = valid_actions.enemies
    focus = _focus_target(me, enemies, game_ctx, allies)
    threatened_by = _who_threatens_me(me, enemies, allies)
    actions: list[dict[str, Any] | None] = []

    picked = _pick_killshots(killshots, enemies, threatened_by, game_ctx)
    if len(picked) >= 2:
        for shot in picked:
            actions.append({"action": "fire", "die": shot["die"], "direction": shot["direction"]})
        return _finalize(actions, valid_actions, me, enemies, game_ctx, allies)

    if len(picked) == 1:
        shot = picked[0]
        actions.append({"action": "fire", "die": shot["die"], "direction": shot["direction"]})
        remaining_die = 2 if shot["die"] == 1 else 1
        unrelated = any(
            not _threat_matches_target(t, shot["target"]) for t in threatened_by
        )
        if threatened_by and unrelated:
            flee = _best_escape(
                me, enemies, valid_actions, remaining_die, game_ctx, focus, allies
            )
            if flee:
                actions.append(flee)
        else:
            reposition = _best_reposition(me, enemies, valid_actions, remaining_die, focus, game_ctx)
            if reposition:
                actions.append(reposition)
        return _finalize(actions, valid_actions, me, enemies, game_ctx, allies)

    if threatened_by:
        for first, second in ((1, 2), (2, 1)):
            e1 = _best_escape(me, enemies, valid_actions, first, game_ctx, focus, allies)
            if not e1:
                continue
            actions.append(e1)
            die_used = valid_actions.die1 if first == 1 else valid_actions.die2
            if die_used is None:
                return _finalize(actions, valid_actions, me, enemies, game_ctx, allies)
            nx, ny = step(me.x, me.y, e1["direction"], die_used.value)
            e2 = _best_escape_from(
                nx, ny, enemies, valid_actions, second, game_ctx, focus, allies
            )
            if e2:
                actions.append(e2)
            return _finalize(actions, valid_actions, me, enemies, game_ctx, allies)
        return _finalize(actions, valid_actions, me, enemies, game_ctx, allies)

    for first, second in ((1, 2), (2, 1)):
        r1 = _best_reposition(me, enemies, valid_actions, first, focus, game_ctx)
        if not r1:
            continue
        actions.append(r1)
        die_used = valid_actions.die1 if first == 1 else valid_actions.die2
        if die_used is None:
            return _finalize(actions, valid_actions, me, enemies, game_ctx, allies)
        nx, ny = step(me.x, me.y, r1["direction"], die_used.value)
        r2 = _best_reposition_from(nx, ny, enemies, valid_actions, second, focus, game_ctx)
        if r2:
            actions.append(r2)
        return _finalize(actions, valid_actions, me, enemies, game_ctx, allies)

    return _finalize(actions, valid_actions, me, enemies, game_ctx, allies)


def _best_escape(
    me: Any,
    enemies: list[Any],
    valid_actions: Any,
    die_index: int,
    game_ctx: Any | None,
    focus: Any | None,
    allies: frozenset[str],
):
    return _best_escape_from(
        me.x, me.y, enemies, valid_actions, die_index, game_ctx, focus, allies
    )


def _best_escape_from(
    x: int,
    y: int,
    enemies: list[Any],
    valid_actions: Any,
    die_index: int,
    game_ctx: Any | None,
    focus: Any | None,
    allies: frozenset[str],
):
    die = valid_actions.die1 if die_index == 1 else valid_actions.die2
    if die is None:
        return None
    enemy_positions = {(e.x, e.y) for e in enemies}
    next_t = _next_opponent_tank(enemies, game_ctx)
    best_dir = None
    best_score = -10**9

    for direction in die.valid_moves:
        nx, ny = step(x, y, direction, die.value)
        if (nx, ny) in enemy_positions:
            continue
        score = _safety_score(nx, ny, enemies)
        if focus is not None:
            score += _offensive_score(nx, ny, enemies, die.value, focus) // 4
        if next_t is not None:
            skip_next_penalty = (
                allies
                and _has_outsiders(enemies, allies)
                and _is_ally(next_t, allies)
            )
            if not skip_next_penalty:
                score -= _incoming_from_tank_at(next_t, nx, ny)
        if score > best_score:
            best_score = score
            best_dir = direction

    if best_dir:
        return {"action": "move", "die": die_index, "direction": best_dir}
    return None


def _best_reposition(me: Any, enemies: list[Any], valid_actions: Any, die_index: int, focus: Any | None, game_ctx: Any | None):
    return _best_reposition_from(me.x, me.y, enemies, valid_actions, die_index, focus, game_ctx)


def _best_reposition_from(
    x: int,
    y: int,
    enemies: list[Any],
    valid_actions: Any,
    die_index: int,
    focus: Any | None,
    game_ctx: Any | None,
):
    del game_ctx  # reserved for future (e.g. next-player offensive pressure)
    die = valid_actions.die1 if die_index == 1 else valid_actions.die2
    if die is None:
        return None
    enemy_positions = {(e.x, e.y) for e in enemies}
    best_dir = None
    best_score = -10**9

    for direction in die.valid_moves:
        nx, ny = step(x, y, direction, die.value)
        if (nx, ny) in enemy_positions:
            continue
        score = _offensive_score(nx, ny, enemies, die.value, focus)
        if score > best_score:
            best_score = score
            best_dir = direction

    if best_dir:
        return {"action": "move", "die": die_index, "direction": best_dir}
    return None


def _safety_score(x: int, y: int, enemies: list[Any]) -> int:
    total = 0
    for enemy in enemies:
        dx = abs(x - enemy.x)
        dy = abs(y - enemy.y)
        total += max(dx, dy)
    return total


def _chebyshev(a: int, b: int, c: int, d: int) -> int:
    return max(abs(a - c), abs(b - d))


def _offensive_score(x: int, y: int, enemies: list[Any], die_value: int, focus: Any | None) -> int:
    """Prefer moves that set up shots; always nudge toward focus when off-axis."""
    score = 0
    for enemy in enemies:
        _, dist = direction_and_distance(x, y, enemy.x, enemy.y)
        if dist is not None and dist == die_value:
            threat_value = 6 - enemy.score
            sc = 10 + threat_value * 5
            if focus is not None and _same_tank(enemy, focus):
                sc += 22
            score += sc
        elif dist is not None:
            sc = 1
            if focus is not None and _same_tank(enemy, focus):
                sc += 5
            # Same ray but wrong range — reward being closer in steps along that axis
            gap = abs(dist - die_value)
            score += sc + max(0, 8 - gap)
        else:
            # Off the attack ray: old code scored 0 → random wandering. Pull toward focus.
            d0 = _chebyshev(x, y, enemy.x, enemy.y)
            score += max(0, 14 - d0)
            if focus is not None and _same_tank(enemy, focus):
                score += max(0, 10 - d0 // 2)

    return score
