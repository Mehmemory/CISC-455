from utils import Point, TileType, _grid_from_state_str, _grid_to_state_str

import json
import copy

class Puzzle:
    def __init__(self, num_rows, num_cols, grid, num_walls):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.grid = grid
        self.horse_pos = None

        num_horses = 0

        for i in range(num_cols):
            for j in range(num_rows):
                if grid[i][j] == TileType.HORSE:
                    if num_horses != 0:
                        raise Exception("Puzzle cannot have multiple horses.")
                    num_horses += 1
                    self.horse_pos = Point(i, j)

        self.num_walls = num_walls

    @classmethod
    def from_json(cls, json_str):
        obj = json.loads(json_str)

        num_rows = obj["num_rows"]
        num_cols = obj["num_cols"]
        grid = _grid_from_state_str(obj["grid"], num_rows, num_cols)
        num_walls = obj["num_walls"]

        return cls(num_rows, num_cols, grid, num_walls)

    def to_json(self):
        obj = dict(
            num_rows=self.num_rows,
            num_cols=self.num_cols,
            num_walls=self.num_walls,
            horse_pos=(self.horse_pos.x, self.horse_pos.y),
            grid=_grid_to_state_str(self.grid, self.num_rows, self.num_cols),
        )

        return json.dumps(obj, separators=(",", ":"))

    def to_json_with_solution(self, solution):
        temp_grid = copy.deepcopy(self.grid)

        for wall in solution:
            temp_grid[wall.x][wall.y] = TileType.WALL

        obj = dict(
            num_rows=self.num_rows,
            num_cols=self.num_cols,
            num_walls=self.num_walls,
            horse_pos=(self.horse_pos.x, self.horse_pos.y),
            grid=_grid_to_state_str(temp_grid, self.num_rows, self.num_cols),
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

