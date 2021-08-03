from __future__ import annotations
from game_map import GameMap
from typing import Iterator, Tuple
import random
import tcod
import entity_factories


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    @property
    def cells(self):
        return [
            (x, y)
            for x in range(self.x1 + 1, self.x2)
            for y in range(self.y1 + 1, self.y2)
        ]

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def place_entities(
    room, dungeon: GameMap, maximum_monsters: int, maximum_items: int
) -> None:
    number_monsters = random.randint(0, maximum_monsters)
    number_of_items = random.randint(0, maximum_items)

    for _i in range(number_monsters):
        x, y = random.choice(room)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            if random.random() < 0.8:
                entity_factories.goblin.spawn(dungeon, x, y)
            else:
                entity_factories.orc.spawn(dungeon, x, y)

    for _i in range(number_of_items):
        x, y = random.choice(room)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            item_chance = random.random()

            if item_chance < 0.7:
                entity_factories.health_potion.spawn(dungeon, x, y)
            elif item_chance < 0.8:
                entity_factories.fireball_scroll.spawn(dungeon, x, y)
            elif item_chance < 0.9:
                entity_factories.confusion_scroll.spawn(dungeon, x, y)
            else:
                entity_factories.lightning_scroll.spawn(dungeon, x, y)
