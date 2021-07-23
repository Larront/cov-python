from typing import List

from map_builders.map_builder import MapBuilder
from map_builders.common import RectangularRoom, tunnel_between, place_entities

from game_map import GameMap
import tile_types
import random

from engine import Engine


class SimpleMapBuilder(MapBuilder):
    def __init__(self, max_rooms: int, room_min_size: int, room_max_size: int, map_width: int, map_height: int, max_monsters_room: int, engine: Engine):
        super().__init__(
            max_rooms, room_min_size, room_max_size, map_width, map_height, max_monsters_room, engine)

    def build(self) -> GameMap:
        """Generate a new dungeon map."""
        player = self.engine.player
        dungeon = GameMap(self.engine, self.map_width, self.map_height,
                          entities=[player])

        rooms: List[RectangularRoom] = []

        for r in range(self.max_rooms):
            room_width = random.randint(self.room_min_size, self.room_max_size)
            room_height = random.randint(
                self.room_min_size, self.room_max_size)

            x = random.randint(0, dungeon.width - room_width - 1)
            y = random.randint(0, dungeon.height - room_height - 1)

            # "RectangularRoom" class makes rectangles easier to work with
            new_room = RectangularRoom(x, y, room_width, room_height)

            # Run through the other rooms and see if they intersect with this one.
            if any(new_room.intersects(other_room) for other_room in rooms):
                continue  # This room intersects, so go to the next attempt.
            # If there are no intersections then the room is valid.

            # Dig out this rooms inner area.
            dungeon.tiles[new_room.inner] = tile_types.floor

            if len(rooms) == 0:
                # The first room, where the player starts.
                player.place(*new_room.center, dungeon)
            else:  # All rooms after the first.
                # Dig out a tunnel between this room and the previous one.
                for x, y in tunnel_between(rooms[-1].center, new_room.center):
                    dungeon.tiles[x, y] = tile_types.floor

            place_entities(new_room, dungeon, self.max_monsters_room)

            # Finally, append the new room to the list.
            rooms.append(new_room)

        return dungeon
