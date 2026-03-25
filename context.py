"""Full-game snapshot for multiplayer-aware strategy (turn order, standings)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GameContext:
    my_tank_id: str
    turn_order: list[str]
    tanks: dict[str, dict[str, Any]]

    @classmethod
    def from_game_state(cls, state: dict[str, Any], my_tank_name: str) -> GameContext | None:
        tanks = state.get("tanks") or {}
        if not isinstance(tanks, dict):
            return None
        my_id = next(
            (tid for tid, t in tanks.items() if isinstance(t, dict) and t.get("name") == my_tank_name),
            None,
        )
        if my_id is None:
            return None
        order = state.get("turnOrder") or []
        if not isinstance(order, list):
            order = []
        return cls(my_tank_id=my_id, turn_order=[str(x) for x in order], tanks=dict(tanks))

    def my_score(self) -> int:
        t = self.tanks.get(self.my_tank_id) or {}
        return int(t.get("score", 0))

    def max_other_score(self) -> int:
        scores = [
            int(t.get("score", 0))
            for tid, t in self.tanks.items()
            if tid != self.my_tank_id and isinstance(t, dict)
        ]
        return max(scores, default=0)

    def i_am_behind_leader(self) -> bool:
        return self.my_score() < self.max_other_score()

    def next_player_id_after_me(self) -> str | None:
        if not self.turn_order or self.my_tank_id not in self.turn_order:
            return None
        idx = self.turn_order.index(self.my_tank_id)
        return self.turn_order[(idx + 1) % len(self.turn_order)]

    def tank_dict(self, tank_id: str) -> dict[str, Any] | None:
        t = self.tanks.get(tank_id)
        return t if isinstance(t, dict) else None
