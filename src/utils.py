from enum import Enum

# Classes and enums
class TileType(Enum):
    SPACE = 0
    WATER = 1
    WALL = 2
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

def _grid_to_state_str(grid, num_rows, num_cols):
    state_str = "".join(["".join([str(grid[j][i].value) for j in range(num_cols)]) for i in range(num_rows)])
    return state_str

def _grid_from_state_str(state_str, num_rows, num_cols):
    if len(state_str) != num_cols * num_rows:
        raise Exception("Grid state string does not have the current length.")

    grid = [[None for _ in range(num_rows)] for _ in range(num_cols)]

    l = 0
    for j in range(num_rows):
        for i in range(num_cols):
            grid[i][j] = TileType(int(state_str[l]))
            l += 1

    return grid