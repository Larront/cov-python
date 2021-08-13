from __future__ import annotations
from typing import Iterator, TYPE_CHECKING, Tuple, List, Dict
import tcod
from scipy import spatial
import numpy as np

import entity_factories
import random
from game_map import GameMap
from spawn_table import (
    max_items_by_floor,
    max_monsters_by_floor,
    enemy_chances,
    item_chances,
)
import tile_types

if TYPE_CHECKING:
    from entity import Entity


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


def generate_dijkstra_map(dungeon: GameMap, point: Tuple[int, int]):
    cost = np.where(dungeon.tiles == tile_types.floor, 1, 0)

    dist = tcod.path.maxarray((dungeon.width, dungeon.height), dtype=np.int32)
    dist[point] = 0

    tcod.path.dijkstra2d(dist, cost, 1, None, out=dist)

    return dist


def exit_from_dijk(dungeon: GameMap, dijk_map, cull_unreachable=False):
    exit_tile = ((0, 0), 0.0)

    for y in range(0, dungeon.height):
        for x in range(0, dungeon.width):
            if dungeon.tiles[x, y] == tile_types.floor:
                dist_to_start = dijk_map[x, y]

                if dist_to_start == np.iinfo(np.int32).max:
                    if cull_unreachable:
                        dungeon.tiles[x, y] = tile_types.wall
                else:
                    if dist_to_start > exit_tile[1]:
                        exit_tile = ((x, y), dist_to_start)

    return exit_tile[0]


def place_entities(
    cells,
    dungeon: GameMap,
    floor_number: int,
) -> None:

    number_of_monsters = dungeon.engine.rng.integers(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number), endpoint=True
    )
    number_of_items = dungeon.engine.rng.integers(
        0, get_max_value_for_floor(max_items_by_floor, floor_number), endpoint=True
    )

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, dungeon, floor_number
    )
    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, dungeon, floor_number
    )

    for entity in monsters + items:
        x, y = dungeon.engine.rng.choice(cells)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)


def get_max_value_for_floor(
    max_value_by_floor: List[Tuple[int, int]], floor: int
) -> int:
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value


def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
    number_of_entities: int,
    dungeon: GameMap,
    floor: int,
) -> List[Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())
    normalized_weights = entity_weighted_chance_values / np.linalg.norm(
        entity_weighted_chance_values
    )

    chosen_entities = dungeon.engine.rng.choice(
        entities, p=normalized_weights, size=number_of_entities
    )

    return chosen_entities.tolist()
