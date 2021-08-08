import tcod
import numpy as np

from map_builders.map_builder import MapBuilder
from map_builders.common import (
    place_entities,
    generate_voronoi_regions,
    generate_dijkstra_map,
    exit_from_dijk,
)

from game_map import GameMap
import tile_types

from engine import Engine


class CellularMapBuilder(MapBuilder):
    def __init__(
        self,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        max_monsters_room: int,
        max_items_room: int,
        engine: Engine,
    ):
        super().__init__(
            max_rooms,
            room_min_size,
            room_max_size,
            map_width,
            map_height,
            max_monsters_room,
            max_items_room,
            engine,
        )

    def build(self) -> GameMap:
        """Generate a new dungeon map."""
        player = self.engine.player
        dungeon = GameMap(
            self.engine, self.map_width, self.map_height, entities=[player]
        )

        dungeon.tiles = self.engine.rng.choice(
            [tile_types.wall, tile_types.floor],
            size=(self.map_width, self.map_height),
            p=[0.55, 0.45],
        )

        for i in range(0, 10):
            new_tiles = dungeon.tiles.copy()

            for y in range(1, self.map_height - 1):
                for x in range(1, self.map_width - 1):
                    neighbors = self.getAdjacentWalls(x, y, dungeon)

                    if neighbors > 4 or neighbors == 0:
                        new_tiles[x, y] = tile_types.wall
                    else:
                        new_tiles[x, y] = tile_types.floor

            dungeon.tiles = new_tiles.copy()

        for y in range(0, self.map_height):
            for x in range(0, self.map_width):
                if x < 1 or x > self.map_width - 2 or y < 1 or y > self.map_height - 2:
                    dungeon.tiles[x, y] = tile_types.wall

        player.place(int(self.map_width / 2), int(self.map_height / 2), dungeon)
        while dungeon.tiles[player.x, player.y] == tile_types.wall:
            player.place(player.x - 1, player.y, dungeon)

        dijk_map = generate_dijkstra_map(dungeon, (player.x, player.y))
        exit_tile = exit_from_dijk(dungeon, dijk_map, cull_unreachable=True)

        dungeon.tiles[exit_tile] = tile_types.down_stairs
        dungeon.downstairs = exit_tile
        regions = generate_voronoi_regions(dungeon)

        for region in regions:
            if len(region) > 0:
                place_entities(
                    region,
                    dungeon,
                    self.max_monsters_room + 3,
                    self.max_items_room,
                )

        return dungeon
