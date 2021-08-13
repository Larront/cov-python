from typing import List
from scipy.ndimage.measurements import label

from tcod.event import wait

from map_builders.map_builder import MapBuilder
from map_builders.common import RectangularRoom, tunnel_between, place_entities

from game_map import GameMap
import tile_types
import numpy as np
from scipy import ndimage

from engine import Engine


class EvilCellularMapBuilder(MapBuilder):
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

        rooms: List[RectangularRoom] = []

        dungeon.tiles = self.engine.rng.choice(
            [tile_types.wall, tile_types.floor],
            size=(self.map_width, self.map_height),
            p=[0.6, 0.4],
        )

        for y in range(0, self.map_height):
            for x in range(0, self.map_width):
                if x < 2 or x > self.map_width - 3 or y < 2 or y > self.map_height - 3:
                    dungeon.tiles[x, y] = tile_types.wall

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

        for y in range(0, self.map_height - 1):
            for x in range(0, self.map_width - 1):
                if x < 2 or x > self.map_width - 3 or y < 2 or y > self.map_height - 3:
                    dungeon.tiles[x, y] = tile_types.wall

        self.cleanup(dungeon, 1)

        bool = dungeon.tiles == tile_types.floor

        # Find and connect each blob
        labels, nlabels = ndimage.label(bool)
        r, c = np.vstack(ndimage.center_of_mass(bool, labels, np.arange(nlabels) + 1)).T

        for i in range(1, len(r)):
            for x, y in tunnel_between(
                [int(r[i]), int(c[i])], [int(r[i - 1]), int(c[i - 1])], dungeon
            ):
                dungeon.tiles[x, y] = tile_types.floor

        cells = [
            (x, y)
            for x in range(0, self.map_width - 1)
            for y in range(0, self.map_height - 1)
            if dungeon.tiles[x, y] == tile_types.floor
        ]

        place_entities(cells, dungeon, self.engine.game_world.current_floor)

        player.place(int(r[0]), int(c[0]), dungeon)

        return dungeon
