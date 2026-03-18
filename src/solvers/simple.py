from solver import PuzzleSolver
from utils import Point, TileType

import random
import copy
from collections import deque

FITNESS_EXPONENT = 2
MUTATION_DISPLACEMENT_RADIUS = 2

class SimpleSolutionStats:
    def __init__(self, tile_count, apple_count, cherry_count, bees_count):
        self.tile_count = tile_count
        self.apple_count = apple_count
        self.cherry_count = cherry_count
        self.bees_count = bees_count

def fitness(solver, solution):
    # Calculates fitness based on the number of reachable exits and how long they take to get them compared to a default board
    # If the horse is fully enclosed, adds additional fitness for each tile and item enclosed
    # defaultEscapes is a tuple list with 		[0] = coordinates       and 	[1] = depth

    fitness = 0

    # run flood fill on the board:
    flood, stats = solver._flood_fill(solution)

    # print("\n".join([" ".join([chr(flood[j][i] + ord("0")) if flood[j][i] != -1 else "X" for j in range(solver.puzzle.num_cols)]) for i in range(solver.puzzle.num_rows)]))

    # Subtract fitness based on how many escapes possible and how long (compared to default) it takes to get to each
    for pos, dist in solver._default_exits:
        if flood[pos.x][pos.y] == -1:
            fitness += 1
        else:
            diff = flood[pos.x][pos.y] - dist # compares distance
            fitness += 1 - (0.5)**(diff)
            # print(pos, dist, fitness, dist, flood[pos.x][pos.y])

    # for solutions with no escapes, add the number of enclosed tiles to the fitness:
    if fitness == len(solver._default_exits):
        fitness += stats.tile_count + 3 * stats.cherry_count + 10 * stats.apple_count + 5 * stats.bees_count

    return fitness**FITNESS_EXPONENT

def mutate(solver, solution):
    # TODO: convert this to ES based mutation with varying displacement radius
    new_solution = []

    occupied_walls = copy.deepcopy(solution)

    for wall in solution:
        if random.random() >= solver.individual_mutation_rate:
            new_solution.append(wall)
            continue

        possible_positions = []
        for i in range(-MUTATION_DISPLACEMENT_RADIUS, MUTATION_DISPLACEMENT_RADIUS+1):
            for j in range(-MUTATION_DISPLACEMENT_RADIUS, MUTATION_DISPLACEMENT_RADIUS+1):
                new_wall = Point(wall.x + i, wall.y + j)
                if solver._is_tile_in_grid(new_wall) and not solver._is_tile_blocked(new_wall) and new_wall not in occupied_walls:
                    possible_positions.append(new_wall)

        if possible_positions != []:
            displaced_wall = random.choice(possible_positions)
            new_solution.append(displaced_wall)

            occupied_walls.remove(wall)
            occupied_walls.add(displaced_wall)
        else:
            new_solution.append(wall)

    return set(new_solution)

def crossover(solver, *solution):
    return solution


class SimpleSolver(PuzzleSolver):
    def __init__(self, puzzle, population_size, mutation_rate, individual_mutation_rate, mating_pool_size, mutate_func=mutate, fitness_func=fitness, crossover_func=crossover):
        super().__init__(puzzle)

        self.generation = 0
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.individual_mutation_rate = individual_mutation_rate
        self.mating_pool_size = mating_pool_size
        self.population = []
        self.mutate = mutate_func
        self.fitness = fitness_func
        self.crossover = crossover_func

        self._valid_wall_positions = puzzle.valid_wall_positions()
        self._weights = range(1, population_size + 1)
        self._default_exits = []
        default_dist, _ = self._flood_fill()

        for i in range(0, puzzle.num_cols - 1):
            pos = Point(i, 0)
            if not self._is_tile_blocked(pos):
                self._default_exits.append((pos, default_dist[pos.x][pos.y]))

        for j in range(0, puzzle.num_rows - 1):
            pos = Point(puzzle.num_cols - 1, j)
            if not self._is_tile_blocked(pos):
                self._default_exits.append((pos, default_dist[pos.x][pos.y]))

        for i in range(0, puzzle.num_cols - 1):
            pos = Point(puzzle.num_cols - 1 - i, puzzle.num_rows - 1)
            if not self._is_tile_blocked(pos):
                self._default_exits.append((pos, default_dist[pos.x][pos.y]))

        for j in range(0, puzzle.num_rows - 1):
            pos = Point(0, puzzle.num_rows - 1 - i)
            if not self._is_tile_blocked(pos):
                self._default_exits.append((pos, default_dist[pos.x][pos.y]))


    def print_setup(self):
        print("SimpleSolver")
        print("=" * 80)
        print(f"Population size: {self.population_size}")
        print(f"Mutation rate: {self.mutation_rate}")
        print(f"Individual mutation rate: {self.individual_mutation_rate}")
        print(f"Mating pool size: {self.mating_pool_size}")
        print("Puzzle:")
        self.puzzle.pprint()
        print("=" * 80)

    def initialize_population(self):
        self.population = []
        for _ in range(self.population_size):
            random_wall_positions = self._random_solution()
            self.population.append((random_wall_positions, self.fitness(self, random_wall_positions)) )

    def _random_solution(self):
        return set(random.sample(self._valid_wall_positions, self.puzzle.num_walls))

    def run_generation(self):
        # Sort current population by fitness
        candidates = sorted(copy.deepcopy(self.population), key=lambda s: s[1])

        # Select individuals by rank into the mating pool
        # mating_pool = random.choices(candidates, weights=self._weights, k=self.mating_pool_size)

        offspring = []

        for sol, fitness in candidates:
            if random.random() < self.mutation_rate:
                mutated_sol = self.mutate(self, sol)
                # print(f"sol: {sol}, mutated_sol: {mutated_sol}")
                offspring.append((mutated_sol, self.fitness(self, mutated_sol)))
            else:
                offspring.append((sol, fitness))

        self.population = offspring

        self.generation += 1

    def pprint_solution(self, solution):
        temp_grid = copy.deepcopy(self.puzzle.grid)

        for wall in solution:
            temp_grid[wall.x][wall.y] = TileType.WALL

        solution_str = "\n".join(["".join([temp_grid[j][i].to_char() for j in range(self.puzzle.num_cols)]) for i in range(self.puzzle.num_rows)])
        print(solution_str)

    def best_solution(self):
        return max(self.population, key=lambda s: s[1])

    def _is_tile_in_grid(self, pos):
        return 0 <= pos.x < self.puzzle.num_cols and 0 <= pos.y < self.puzzle.num_rows

    def _is_tile_blocked(self, pos, solution=None):
        if solution is None:
            return self.puzzle.get_tile_from_point(pos) == TileType.WATER
        else:
            return pos in solution or self.puzzle.get_tile_from_point(pos) == TileType.WATER

    def _is_tile_on_edge(self, pos):
        # returns true if a given pos is on the edge of the puzzle
        return pos.x == 0 or pos.y == 0 or pos.x == self.puzzle.num_cols - 1 or pos.y == self.puzzle.num_rows - 1

    def _flood_fill(self, solution=None):
        # returns a 2d array the corresponds to how many steps it takes to reach each tile of the puzzleLayout
        # -1 means the tile is unreachable:

        dist = [[-1 for _ in range(self.puzzle.num_rows)] for _ in range(self.puzzle.num_cols)]	# initialize the array with all -1's
        dirs = [Point(-1, 0), Point(1, 0), Point(0, -1), Point(0, 1)] # cache directions

        queue = deque() # stores which tile to check next
        horse_pos = self.puzzle.horse_pos
        stats = SimpleSolutionStats(0, 0, 0, 0)

        if not self._is_tile_on_edge(horse_pos):
            queue.append((horse_pos, 0)) # add startpos to the queue and note that it takes 0 steps to get there
            dist[horse_pos.x][horse_pos.y] = 0

        while len(queue) > 0:
            curr_pos, curr_dist = queue.popleft()
            stats.tile_count += 1

            for dir in dirs: # checks each neighbor around current
                next_pos = curr_pos + dir

                # skip tile if it is not inside the grid or has already been visited
                if not self._is_tile_in_grid(next_pos) or dist[next_pos.x][next_pos.y] != -1:
                    continue

                # if the tile is not blocked.
                if not self._is_tile_blocked(next_pos, solution):
                    new_dist = curr_dist + 1
                    dist[next_pos.x][next_pos.y] = new_dist # update distance

                    match self.puzzle.get_tile_from_point(curr_pos):
                        case TileType.APPLE:
                            stats.apple_count += 1
                        case TileType.BEES:
                            stats.bees_count += 1
                        case TileType.CHERRY:
                            stats.cherry_count += 1

                    queue.append((next_pos, new_dist))

        return dist, stats