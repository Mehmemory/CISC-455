from utils import Point, TileType
import json

class Puzzle:
    def __init__(self, num_rows, num_cols, grid, num_walls):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.grid = grid
        self.horse_pos = None

        num_horses = 0

        for i in range(num_cols):
            for j in range(num_rows):
                grid[i][j] = TileType(grid[i][j])

                if grid[i][j] == TileType.HORSE:
                    if num_horses != 0:
                        raise Exception("Puzzle cannot have multiple horses.")
                    num_horses += 1
                    self.horse_pos = Point(i, j)

        self.num_walls = num_walls

    def _grid_from_state_str(self, state_str):
        if len(state_str) != self.num_cols * self.num_rows:
            raise Exception("Grid state string does not have the current length.")

        grid = [[None for _ in range(num_rows)] for _ in range(num_cols)]
        l = 0

        for i in range(num_cols):
            for j in range(num_rows):
                grid[i][j] = TileType(state_str[l])
                l += 1

        return grid

    def _grid_to_state_str(self):
        state_str = "".join(["".join([self.grid[j][i].value for j in range(self.num_cols)]) for i in range(self.num_rows)])
        return state_str

    @classmethod
    def fromJSON(cls, json_str):
        obj = json.loads(json_str)

        num_rows = obj["num_rows"]
        num_cols = obj["num_cols"]
        grid = self._grid_from_state_str(obj["grid"])
        num_walls = obj["num_walls"]

        return cls(**obj)

    def toJSON(self):
        obj = dict(
            num_rows=self.num_rows,
            num_cols=self.num_cols,
            num_walls=self.num_walls,
            horse_pos=(self.horse_pos.x, self.horse_pos.y),
            grid=self._grid_to_state_str(),
        )

        return json.dumps(obj, separators=(",", ":"))

    def get_tile_from_point(self, pos):
        return self.get_tile(pos.x, pos.y)

    def get_tile(self, x, y):
        return self.grid[x][y]

    def valid_wall_positions(self):
        valid_wall_positions = []

        for i in range(self.num_cols):
            for j in range(self.num_rows):
                if self.grid[i][j] == TileType.SPACE:
                    valid_wall_positions.append(Point(i, j))

        return valid_wall_positions

    def pprint(self):
        puzzle_str = "\n".join(["".join([self.grid[j][i].to_char() for j in range(self.num_cols)]) for i in range(self.num_rows)])
        print(puzzle_str)

