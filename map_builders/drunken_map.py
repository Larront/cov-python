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


class Generation(Enum):
    OPEN_AREA = 1
    OPEN_HALLS = 2
    WINDING_PASSAGES = 3


class DrunkenMapBuilder(MapBuilder):
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
        generation = self.engine.rng.choice(Generation)
        if generation == Generation.OPEN_AREA:
            self.spawn_mode = "Start"
            self.drunk_life = 400
            self.floor_percent = 0.5
        elif generation == Generation.OPEN_HALLS:
            self.spawn_mode = "Random"
            self.drunk_life = 400
            self.floor_percent = 0.5
        elif generation == Generation.WINDING_PASSAGES:
            self.spawn_mode = "Random"
            self.drunk_life = 100
            self.floor_percent = 0.4
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

        total_tiles = self.map_width * self.map_height
        desired_tiles = int(total_tiles * self.floor_percent)
        digger_count = 0

        floor_number = len(
            [
                (x, y)
                for x in range(0, self.map_width - 1)
                for y in range(0, self.map_height - 1)
                if dungeon.tiles[x, y] == tile_types.floor
            ]
        )

        while floor_number < desired_tiles:
            if self.spawn_mode == "Random":
                if digger_count == 0:
                    drunk_x = start_pos[0]
                    drunk_y = start_pos[1]
                else:
                    drunk_x = self.engine.rng.integers(1, self.map_width - 1)
                    drunk_y = self.engine.rng.integers(1, self.map_height - 1)
            else:
                drunk_x = start_pos[0]
                drunk_y = start_pos[1]

            drunk_life = 400

            while drunk_life > 0:
                dungeon.tiles[drunk_x, drunk_y] = tile_types.floor

                stagger_direction = self.engine.rng.integers(0, 4)
                if stagger_direction == 0 and drunk_x > 1:
                    drunk_x -= 1
                elif stagger_direction == 1 and drunk_x < self.map_width - 2:
                    drunk_x += 1
                elif stagger_direction == 2 and drunk_y > 1:
                    drunk_y -= 1
                elif stagger_direction == 3 and drunk_y < self.map_height - 2:
                    drunk_y += 1

                drunk_life -= 1

            digger_count += 1
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
