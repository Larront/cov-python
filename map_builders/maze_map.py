from dataclasses import dataclass
from typing import Optional, Tuple

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


class MazeMapBuilder(MapBuilder):
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

        self.field = []

        for y in range(self.map_height):
            row = []
            for x in range(self.map_width):
                row.append("?")
            self.field.append(row)

        self.frontier = []

        start_x = self.engine.rng.integers(0, self.map_width)
        start_y = self.engine.rng.integers(0, self.map_height)
        self.carve(start_y, start_x)

        branchrate = self.engine.rng.integers(-10, 11)

        from math import e

        while len(self.frontier):
            # select a random edge
            pos = self.engine.rng.random()
            pos = pos ** (e ** -branchrate)
            choice = self.frontier[int(pos * len(self.frontier))]
            if self.check(*choice):
                self.carve(*choice)
            else:
                self.harden(*choice)
            self.frontier.remove(choice)

        # set unexposed cells to be walls
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.field[y][x] == "?":
                    self.field[y][x] = "#"

        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.field[y][x] == "#":
                    dungeon.tiles[x, y] = tile_types.wall
                else:
                    dungeon.tiles[x, y] = tile_types.floor

        for y in range(0, self.map_height):
            for x in range(0, self.map_width):
                if x < 1 or x > self.map_width - 2 or y < 1 or y > self.map_height - 2:
                    dungeon.tiles[x, y] = tile_types.wall

        player.place(start_x, start_y, dungeon)

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

    def carve(self, y, x):
        extra = []
        self.field[y][x] = "."
        if x > 0:
            if self.field[y][x - 1] == "?":
                self.field[y][x - 1] = ","
                extra.append((y, x - 1))
        if x < self.map_width - 1:
            if self.field[y][x + 1] == "?":
                self.field[y][x + 1] = ","
                extra.append((y, x + 1))
        if y > 0:
            if self.field[y - 1][x] == "?":
                self.field[y - 1][x] = ","
                extra.append((y - 1, x))
        if y < self.map_height - 1:
            if self.field[y + 1][x] == "?":
                self.field[y + 1][x] = ","
                extra.append((y + 1, x))
        self.engine.rng.shuffle(extra)
        self.frontier.extend(extra)

    def harden(self, y, x):
        """Make the cell at y,x a wall."""
        self.field[y][x] = "#"

    def check(self, y, x, nodiagonals=True):
        """Test the cell at y,x: can this cell become a space?

        True indicates it should become a space,
        False indicates it should become a wall.
        """

        edgestate = 0
        if x > 0:
            if self.field[y][x - 1] == ".":
                edgestate += 1
        if x < self.map_width - 1:
            if self.field[y][x + 1] == ".":
                edgestate += 2
        if y > 0:
            if self.field[y - 1][x] == ".":
                edgestate += 4
        if y < self.map_height - 1:
            if self.field[y + 1][x] == ".":
                edgestate += 8

        if nodiagonals:
            # if this would make a diagonal connecition, forbid it
            # the following steps make the test a bit more complicated and are not necessary,
            # but without them the mazes don't look as good
            if edgestate == 1:
                if x < self.map_width - 1:
                    if y > 0:
                        if self.field[y - 1][x + 1] == ".":
                            return False
                    if y < self.map_height - 1:
                        if self.field[y + 1][x + 1] == ".":
                            return False
                return True
            elif edgestate == 2:
                if x > 0:
                    if y > 0:
                        if self.field[y - 1][x - 1] == ".":
                            return False
                    if y < self.map_height - 1:
                        if self.field[y + 1][x - 1] == ".":
                            return False
                return True
            elif edgestate == 4:
                if y < self.map_height - 1:
                    if x > 0:
                        if self.field[y + 1][x - 1] == ".":
                            return False
                    if x < self.map_width - 1:
                        if self.field[y + 1][x + 1] == ".":
                            return False
                return True
            elif edgestate == 8:
                if y > 0:
                    if x > 0:
                        if self.field[y - 1][x - 1] == ".":
                            return False
                    if x < self.map_width - 1:
                        if self.field[y - 1][x + 1] == ".":
                            return False
                return True
            return False
        else:
            # diagonal walls are permitted
            if [1, 2, 4, 8].count(edgestate):
                return True
            return False
