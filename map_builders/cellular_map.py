from typing import List

from tcod.event import wait

from map_builders.map_builder import MapBuilder
from map_builders.common import RectangularRoom, tunnel_between, place_entities

from game_map import GameMap
import tile_types
import numpy as np

from engine import Engine


class CellularMapBuilder(MapBuilder):
    def __init__(self, max_rooms: int, room_min_size: int, room_max_size: int, map_width: int, map_height: int, max_monsters_room: int, max_items_room: int, engine: Engine):
        super().__init__(
            max_rooms, room_min_size, room_max_size, map_width, map_height, max_monsters_room, engine)

    def build(self) -> GameMap:
        """Generate a new dungeon map."""
        player = self.engine.player
        dungeon = GameMap(self.engine, self.map_width, self.map_height,
                          entities=[player])

        rooms: List[RectangularRoom] = []

        dungeon.tiles = np.random.choice([tile_types.wall, tile_types.floor], size=(
            self.map_width, self.map_height), p=[0.6, 0.4])

        for y in range(0, self.map_height):
            for x in range(0, self.map_width):
                if x < 2 or x > self.map_width-3 or y < 2 or y > self.map_height-3:
                    dungeon.tiles[x, y] = tile_types.wall

        for i in range(0, 10):
            new_tiles = dungeon.tiles.copy()

            for y in range(1, self.map_height-1):
                for x in range(1, self.map_width-1):
                    neighbors = self.getAdjacentWalls(x, y, dungeon)

                    if neighbors > 4 or neighbors == 0:
                        new_tiles[x, y] = tile_types.wall
                    else:
                        new_tiles[x, y] = tile_types.floor
            dungeon.tiles = new_tiles.copy()

        for y in range(0, self.map_height-1):
            for x in range(0, self.map_width-1):
                if x < 2 or x > self.map_width-3 or y < 2 or y > self.map_height-3:
                    dungeon.tiles[x, y] = tile_types.wall

        self.cleanup(dungeon, 1)

        return dungeon

    def floodFill(self, dungeon, x, y):
        '''
        Flood fill the separate regions of the level, discard
        the regions that are smaller than a minimum size, and
        create a reference for the rest.
        '''
        cave = set()
        tile = (x, y)
        toBeFilled = set([tile])
        while toBeFilled:
            tile = toBeFilled.pop()

            if tile not in cave:
                cave.add(tile)

                self.dungeon.tiles[tile[0], tile[1]] = 1

                # check adjacent cells
                x = tile[0]
                y = tile[1]
                north = (x, y-1)
                south = (x, y+1)
                east = (x+1, y)
                west = (x-1, y)

                for direction in [north, south, east, west]:

                    if self.level[direction[0]][direction[1]] == 0:
                        if direction not in toBeFilled and direction not in cave:
                            toBeFilled.add(direction)

            if len(cave) >= self.ROOM_MIN_SIZE:
                self.caves.append(cave)
