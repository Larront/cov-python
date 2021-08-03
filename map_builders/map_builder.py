from game_map import GameMap
from entity import Entity
from engine import Engine
import tile_types


class MapBuilder:
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
        self.max_rooms = max_rooms
        self.room_min_size = room_min_size
        self.room_max_size = room_max_size
        self.map_width = map_width
        self.map_height = map_height
        self.max_monsters_room = max_monsters_room
        self.max_items_room = max_items_room
        self.engine = engine

    def build(self) -> GameMap:
        """
        interface to generate a new GameMap
        This method must be overridden by MapBuilder subclasses.
        """
        raise NotImplementedError()

    def cleanup(self, dungeon: GameMap, smoothing: int):
        for i in range(0, 5):
            # Look at each cell individually and check for smoothness
            for x in range(1, dungeon.width - 1):
                for y in range(1, dungeon.height - 1):
                    if (dungeon.tiles[x, y] == tile_types.wall) and (
                        self.getAdjacentWalls(x, y, dungeon, simple=True) <= smoothing
                    ):
                        dungeon.tiles[x, y] = tile_types.floor

    def getAdjacentWalls(self, x: int, y: int, dungeon: GameMap, simple=False) -> int:
        neighbors = 0

        if dungeon.tiles[x - 1, y] == tile_types.wall:
            neighbors += 1
        if dungeon.tiles[x + 1, y] == tile_types.wall:
            neighbors += 1
        if dungeon.tiles[x, y - 1] == tile_types.wall:
            neighbors += 1
        if dungeon.tiles[x, y + 1] == tile_types.wall:
            neighbors += 1

        if simple:
            return neighbors

        if dungeon.tiles[x - 1, y - 1] == tile_types.wall:
            neighbors += 1
        if dungeon.tiles[x - 1, y + 1] == tile_types.wall:
            neighbors += 1
        if dungeon.tiles[x + 1, y - 1] == tile_types.wall:
            neighbors += 1
        if dungeon.tiles[x + 1, y + 1] == tile_types.wall:
            neighbors += 1

        return neighbors
