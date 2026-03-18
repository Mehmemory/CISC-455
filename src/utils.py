from enum import Enum

# Classes and enums
class TileType(Enum):
    SPACE = 0
    WALL = 1
    WATER = 2
    CHERRY = 3
    APPLE = 4
    BEES = 5
    HORSE = 6

    def __str__(self):
        return self.name

    def to_char(self):
        match self:
            case TileType.HORSE:
                return 'O'
            case TileType.SPACE:
                return '-'
            case TileType.WATER:
                return '#'
            case TileType.CHERRY:
                return 'C'
            case TileType.APPLE:
                return 'A'
            case TileType.BEES:
                return 'B'
            case TileType.WALL:
                return '+'


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def move(self, x, y):
        self.x += x
        self.y += y
        return self