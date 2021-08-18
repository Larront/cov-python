from enum import Enum
import numpy as np

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


class Algorithm(Enum):
    WALK_INWARDS = 1
    WALK_OUTWARDS = 2
    CENTRAL_ATTRACTOR = 3


class Symmetry(Enum):
    NONE = 0
    HORIZONTAL = 1
    VERTICAL = 2
    BOTH = 3


class DLAMapBuilder(MapBuilder):
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
        self.algorithm = self.engine.rng.choice(Algorithm)
        self.algorithm = Algorithm.WALK_INWARDS
        self.floor_percent = 0.25
        dungeon = self.build_map()

        return dungeon

    def build_map(self) -> GameMap:
        """Generate a new dungeon map."""
        player = self.engine.player
        dungeon = GameMap(
            self.engine, self.map_width, self.map_height, entities=[player]
        )
        start_pos = (int(self.map_width / 2), int(self.map_height / 2))
        player.place(int(self.map_width / 2), int(self.map_height / 2), dungeon)
        dungeon.tiles[start_pos] = tile_types.floor

        total_tiles = self.map_width * self.map_height
        desired_tiles = int(total_tiles * self.floor_percent)

        dla = DLA(self.map_width, self.map_height, 1)
        dla.addPoint(desired_tiles)

        dungeon.tiles = np.where(dla.state, tile_types.floor, tile_types.wall)

        dijk_map = generate_dijkstra_map(dungeon, (player.x, player.y))
        exit_tile = exit_from_dijk(dungeon, dijk_map, cull_unreachable=True)

        dungeon.tiles[exit_tile] = tile_types.down_stairs
        dungeon.downstairs = exit_tile

        regions = generate_voronoi_regions(dungeon)

        for region in regions:
            if len(region) > 0:
                place_entities(region, dungeon, self.engine.game_world.current_floor)

        return dungeon


class DLA:
    def __init__(self, width, height, k):
        self.width = width
        self.height = height
        self.state = np.zeros((width, height), dtype=int)
        self.state[width // 2, height // 2] = 1

        self.xBounds = (width // 2, width // 2)
        self.yBounds = (height // 2, height // 2)

        self.radius = 0
        self.xcenter = int(width // 2)
        self.ycenter = int(height // 2)

        self.k = k

    def getSeed(self):
        """
        Returns a randomly sampled initial position
        for a particle.
        Returns (x, y) tuple
        """

        boundingCircle = self.getBoundingCircle()
        p = np.random.randint(len(boundingCircle))

        return boundingCircle[p]

    def isValid(self, curr):
        """
        Checks wether (x, y) is in grid
        Returns True/False
        """
        x, y = curr
        return x > -1 and x < self.width and y > -1 and y < self.height

    def getAdjacentPoints(self, curr):
        """
        Returns points adjacent to curr within image bounds
        Assumption : Adjacent includes diagonal neighbors (max 8)
                        A|A|A
                        A|X|A
                        A|A|A

        Input args:
            curr : (x, y) tuple
        Returns:
            List of adjacent points
        """

        x, y = curr
        adjacentPoints = [
            (x - 1, y - 1),
            (x - 1, y),
            (x - 1, y + 1),
            (x, y - 1),
            (x, y + 1),
            (x + 1, y - 1),
            (x + 1, y),
            (x + 1, y + 1),
        ]

        # Remove points outside the image
        adjacentPoints = filter(
            lambda x: x[0] > -1
            and x[0] < self.width
            and x[1] > -1
            and x[1] < self.height,
            adjacentPoints,
        )
        return adjacentPoints

    def getBoundingCircle(self):
        """
        Gets bounding circle of current image
        Returns list of points in bounding circle
        """

        points = {}

        y1, y2 = self.ycenter, self.ycenter

        for x in range(self.xcenter - self.radius - 10, self.xcenter + 1):
            while (y1 - self.ycenter) ** 2 + (x - self.xcenter) ** 2 <= (
                self.radius
            ) ** 2:
                y1 -= 1
            k = y1
            while (k - self.ycenter) ** 2 + (x - self.xcenter) ** 2 <= (
                self.radius + 1
            ) ** 2:
                if self.isValid((x, k)):
                    points[(x, k)] = True
                k -= 1

            while (y2 - self.ycenter) ** 2 + (x - self.xcenter) ** 2 <= (
                self.radius
            ) ** 2:
                y2 += 1
            k = y2
            while (k - self.ycenter) ** 2 + (x - self.xcenter) ** 2 <= (
                self.radius + 1
            ) ** 2:
                if self.isValid((x, k)):
                    points[(x, k)] = True
                k += 1

        y1, y2 = self.ycenter, self.ycenter
        for x in range(self.xcenter + self.radius + 10, self.xcenter, -1):
            while (y1 - self.ycenter) ** 2 + (x - self.xcenter) ** 2 <= (
                self.radius
            ) ** 2:
                y1 -= 1
            k = y1
            while (k - self.ycenter) ** 2 + (x - self.xcenter) ** 2 <= (
                self.radius + 1
            ) ** 2:
                if self.isValid((x, k)):
                    points[(x, k)] = True
                k -= 1

            while (y2 - self.ycenter) ** 2 + (x - self.xcenter) ** 2 <= (
                self.radius
            ) ** 2:
                y2 += 1
            k = y2
            while (k - self.ycenter) ** 2 + (x - self.xcenter) ** 2 <= (
                self.radius + 1
            ) ** 2:
                if self.isValid((x, k)):
                    points[(x, k)] = True
                k += 1

        if any(map(lambda x: self.state[x] == 1, points.keys())):
            print("can spawn at marked")

        return list(points.keys())

    def checkIfTerminate(self, curr):
        """
        Check if curr sticks in image.
        Will happen with prob k if any adjacent block is 1

        Input args:
            curr : (x, y) tuple
        Returns True/False
        """
        adjacentPoints = self.getAdjacentPoints(curr)
        return (
            any(map(lambda x: self.state[x] == 1, adjacentPoints))
            and np.random.rand() < self.k
        )

    def getNextPosition(self, curr):
        """
        Get next point. Brownian motion is order 1 markov process

        Input args:
            curr : (x, y) tuple
        Returns:
            (x, y) coordinate of next position
        """

        adjacentPoints = self.getAdjacentPoints(curr)  # List of adjacent points
        adjacentPoints = list(filter(lambda x: self.state[x] == 0, adjacentPoints))
        s = np.random.randint(len(adjacentPoints))  # Get random point
        return adjacentPoints[s]

    def getSurfaceArea(self):
        """
        Get surface area of all points.
        Presently O(m**2), can be done better
        Returns integer
        """

        area = 0
        for i in range(self.width):
            for j in range(self.height):
                if self.state[i, j] == 1:
                    adj = self.getAdjacentPoints((i, j))
                    adj = list(filter(lambda x: self.state[x] == 0, adj))
                    area += len(adj)

        return area

    def getNeighbourCount(self):
        """
        For each cell with 1, count neghbouring cells with 1
        Returns integer
        """

        count = 0
        for i in range(self.width):
            for j in range(self.height):
                if self.state[i, j] == 1:
                    adj = self.getAdjacentPoints((i, j))
                    adj = list(filter(lambda x: self.state[x] == 1, adj))
                    count += len(adj)

        return count

    def addPoint(self, desired_tiles=1):
        """
        Adds a new particle to the matrix
        """

        floor_number = np.count_nonzero(self.state)

        while floor_number < desired_tiles:

            if (floor_number + 1) % 100 == 0:
                print(f"{floor_number}/{desired_tiles}")

            curr = self.getSeed()  # Get initial position

            while not self.checkIfTerminate(curr):
                curr = self.getNextPosition(curr)
                if (curr[0] - self.xcenter) ** 2 + (curr[1] - self.ycenter) ** 2 > (
                    self.radius + 15
                ) ** 2:
                    curr = self.getSeed()  # Go back to random point in bounding circle

            self.state[curr] = 1

            # Update bounds
            x, y = curr

            xmin, xmax = self.xBounds
            xmin = min(xmin, x)
            xmax = max(xmax, x)
            self.xBounds = (xmin, xmax)

            ymin, ymax = self.yBounds
            ymin = min(ymin, y)
            ymax = max(ymax, y)
            self.yBounds = (ymin, ymax)

            # Calculate new radius
            self.xcenter = int((xmax + xmin) / 2)
            self.ycenter = int((ymax + ymin) / 2)
            self.radius = (
                int(((xmax - self.xcenter) ** 2 + (ymax - self.ycenter) ** 2) ** 0.5)
                + 1
            )

            floor_number = np.count_nonzero(self.state)
