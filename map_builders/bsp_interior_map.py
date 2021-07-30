from typing import List, Tuple
from tcod import Bsp

from map_builders.map_builder import MapBuilder
from map_builders.common import RectangularRoom, tunnel_between, place_entities

from game_map import GameMap
import tile_types
import random

from engine import Engine


class BSPInteriorMapBuilder(MapBuilder):
    def __init__(self, max_rooms: int, room_min_size: int, room_max_size: int, map_width: int, map_height: int, max_monsters_room: int, max_items_room: int, engine: Engine):
        super().__init__(
            max_rooms, room_min_size, room_max_size, map_width, map_height, max_monsters_room, engine)

    def build(self) -> GameMap:
        """Generate a new dungeon map."""
        player = self.engine.player
        dungeon = GameMap(self.engine, self.map_width, self.map_height,
                          entities=[player])

        rooms: List[RectangularRoom] = []

        bsp = Bsp(x=0, y=0, width=self.map_width, height=self.map_height)
        bsp.split_recursive(
            depth=5,
            min_width=self.room_min_size + 1,
            min_height=self.room_min_size + 1,
            max_horizontal_ratio=1.5,
            max_vertical_ratio=1.5,
        )

        for node in bsp.pre_order():
            if node.children:
                node1, node2 = node.children

                for x, y in tunnel_between(node_center(node1), node_center(node2)):
                    dungeon.tiles[x, y] = tile_types.floor

                dungeon.tiles[node_center(node1)] = tile_types.center
                dungeon.tiles[node_center(node2)] = tile_types.center

            else:
                room = self.build_room(node)
                rooms.append(room)
                dungeon.tiles[room.inner] = tile_types.floor

                place_entities(room, dungeon, self.max_monsters_room)

        player.place(*rooms[0].center, dungeon)

        return dungeon

    def build_room(self, node: Bsp) -> RectangularRoom:
        room_width = node.width
        room_height = node.height

        x = node.x
        y = node.y

        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        return new_room


def node_center(node: Bsp) -> Tuple[int, int]:
    center_x = int((node.x + node.x + node.width) / 2)
    center_y = int((node.y + node.y + node.height) / 2)

    return center_x, center_y
