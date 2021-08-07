from __future__ import annotations
from typing import Iterator, Tuple
import tcod
from scipy import spatial
import numpy as np

import entity_factories
from game_map import GameMap
import tile_types


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
    start: Tuple[int, int], end: Tuple[int, int], dungeon: GameMap
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if dungeon.engine.rng.random() < 0.5:  # 50% chance.
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


def generate_voronoi_regions(dungeon: GameMap):
    cells = [
        (x, y)
        for x in range(0, dungeon.width - 1)
        for y in range(0, dungeon.height - 1)
    ]
    points = []

    # Randomly generate a list of points
    for i in range(0, dungeon.engine.rng.integers(20, 30)):
        points.append(dungeon.engine.rng.choice(cells))

    # Each point has a list of pixels
    point_pixels = []
    for i in range(len(points)):
        point_pixels.append([])

    # Build a search tree
    tree = spatial.KDTree(points)

    # build a list of pixed coordinates to query
    pixel_coordinates = np.zeros((dungeon.height * dungeon.width, 2))
    i = 0
    for pixel_y_coordinate in range(dungeon.height):
        for pixel_x_coordinate in range(dungeon.width):
            pixel_coordinates[i] = np.array([pixel_x_coordinate, pixel_y_coordinate])
            i = i + 1

    # for each pixel within bounds, determine which point it is closest to and add it to the corresponding list in point_pixels
    [distances, indices] = tree.query(pixel_coordinates)

    i = 0
    for pixel_y_coordinate in range(dungeon.height):
        for pixel_x_coordinate in range(dungeon.width):
            if (
                dungeon.tiles[pixel_x_coordinate, pixel_y_coordinate]
                == tile_types.floor
            ):
                point_pixels[indices[i]].append(
                    (pixel_x_coordinate, pixel_y_coordinate)
                )
                i = i + 1

    return point_pixels


def place_entities(
    room, dungeon: GameMap, maximum_monsters: int, maximum_items: int
) -> None:
    number_monsters = dungeon.engine.rng.integers(0, maximum_monsters)
    number_of_items = dungeon.engine.rng.integers(0, maximum_items)

    for _i in range(number_monsters):
        x, y = dungeon.engine.rng.choice(room)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            if dungeon.engine.rng.random() < 0.8:
                entity_factories.goblin.spawn(dungeon, x, y)
            else:
                entity_factories.orc.spawn(dungeon, x, y)

    for _i in range(number_of_items):
        x, y = dungeon.engine.rng.choice(room)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            item_chance = dungeon.engine.rng.random()

            if item_chance < 0.7:
                entity_factories.health_potion.spawn(dungeon, x, y)
            elif item_chance < 0.8:
                entity_factories.fireball_scroll.spawn(dungeon, x, y)
            elif item_chance < 0.9:
                entity_factories.confusion_scroll.spawn(dungeon, x, y)
            else:
                entity_factories.lightning_scroll.spawn(dungeon, x, y)
