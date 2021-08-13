from enum import Enum

from map_builders.map_builder import MapBuilder
from map_builders.common import (
    exit_from_dijk,
    place_entities,
    generate_voronoi_regions,
    generate_dijkstra_map,
)

from game_map import GameMap
import tile_types

from engine import Engine


class Algorithm(Enum):
    WALK_INWARDS = 1
    WALK_OUTWARDS = 2
    CENTRAL_ATTRACTOR = 3


class Symmetry(Enum):
    NONE = 0
    HORIZONTAL = 1
    VERTICAL = 2
    BOTH = 3


class DLAMapBuilder(MapBuilder):
    def __init__(
        self,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        engine: Engine,
    ):
        super().__init__(
            max_rooms,
            room_min_size,
            room_max_size,
            map_width,
            map_height,
            engine,
        )

    def build(self) -> GameMap:
        self.algorithm = self.engine.rng.choice(Algorithm)
        self.algorithm = Algorithm.WALK_INWARDS
        self.floor_percent = 0.25
        dungeon = self.build_map()

        return dungeon

    def build_map(self) -> GameMap:
        """Generate a new dungeon map."""
        player = self.engine.player
        dungeon = GameMap(
            self.engine, self.map_width, self.map_height, entities=[player]
        )

        player.place(int(self.map_width / 2), int(self.map_height / 2), dungeon)

        start_pos = (int(self.map_width / 2), int(self.map_height / 2))
        dungeon.tiles[start_pos[0], start_pos[1]] = tile_types.floor
        dungeon.tiles[start_pos[0] - 1, start_pos[1]] = tile_types.floor
        dungeon.tiles[start_pos[0] + 1, start_pos[1]] = tile_types.floor
        dungeon.tiles[start_pos[0], start_pos[1] - 1] = tile_types.floor
        dungeon.tiles[start_pos[0], start_pos[1] + 1] = tile_types.floor

        total_tiles = self.map_width * self.map_height
        desired_tiles = int(total_tiles * self.floor_percent)

        floor_number = len(
            [
                (x, y)
                for x in range(0, self.map_width - 1)
                for y in range(0, self.map_height - 1)
                if dungeon.tiles[x, y] == tile_types.floor
            ]
        )

        while floor_number < desired_tiles:
            if self.algorithm == Algorithm.WALK_INWARDS:
                digger_x = self.engine.rng.integers(1, self.map_width - 3) + 1
                digger_y = self.engine.rng.integers(1, self.map_height - 3) + 1
                prev_x = digger_x
                prev_y = digger_y

                while dungeon.tiles[digger_x, digger_y] == tile_types.wall:
                    prev_x = digger_x
                    prev_y = digger_y
                    stagger_dir = self.engine.rng.integers(0, 4)
                    if stagger_dir == 0 and digger_x > 1:
                        digger_x -= 1
                    elif stagger_dir == 1 and digger_x < self.map_width - 2:
                        digger_x += 1
                    elif stagger_dir == 2 and digger_y > 1:
                        digger_y -= 1
                    elif stagger_dir == 3 and digger_y < self.map_height - 2:
                        digger_y += 1
                self.paint(dungeon, prev_x, prev_y)

                floor_number = len(
                    [
                        (x, y)
                        for x in range(0, self.map_width - 1)
                        for y in range(0, self.map_height - 1)
                        if dungeon.tiles[x, y] == tile_types.floor
                    ]
                )

        dijk_map = generate_dijkstra_map(dungeon, (player.x, player.y))
        exit_tile = exit_from_dijk(dungeon, dijk_map, cull_unreachable=True)

        dungeon.tiles[exit_tile] = tile_types.down_stairs
        dungeon.downstairs = exit_tile

        regions = generate_voronoi_regions(dungeon)

        for region in regions:
            if len(region) > 0:
                place_entities(region, dungeon, self.engine.game_world.current_floor)

        return dungeon

    def paint(self, dungeon: GameMap, x: int, y: int):
        dungeon.tiles[x, y] = tile_types.floor
