from game_map import GameMap
from entity import Entity
from engine import Engine


class MapBuilder:
    def __init__(self,
                 max_rooms: int,
                 room_min_size: int,
                 room_max_size: int,
                 map_width: int,
                 map_height: int,
                 max_monsters_room: int,
                 engine: Engine,
                 ):
        self.max_rooms = max_rooms
        self.room_min_size = room_min_size
        self.room_max_size = room_max_size
        self.map_width = map_width
        self.map_height = map_height
        self.max_monsters_room = max_monsters_room
        self.engine = engine

    def build(self) -> GameMap:
        """
        interface to generate a new GameMap
        This method must be overridden by MapBuilder subclasses.
        """
        raise NotImplementedError()
