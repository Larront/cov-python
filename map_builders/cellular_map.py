import tcod
import numpy as np
from scipy.signal import convolve2d

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
        """Generate a new dungeon map."""
        player = self.engine.player
        dungeon = GameMap(
            self.engine, self.map_width, self.map_height, entities=[player]
        )

        is_wall = (
            self.engine.rng.random(
                size=(self.map_width, self.map_height), dtype=np.float32
            )
            > 0.55
        )

        for _ in range(0, 10):
            neighbors = convolve2d(is_wall, [[1, 1, 1], [1, 0, 1], [1, 1, 1]], "same")
            is_wall = (neighbors > 4) | (neighbors == 0)

        is_wall[0, :] = True
        is_wall[-1, :] = True
        is_wall[:, 0] = True
        is_wall[:, -1] = True

        dungeon.tiles[:] = np.where(is_wall, tile_types.wall, tile_types.floor)

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
                place_entities(region, dungeon, self.engine.game_world.current_floor)

        return dungeon
