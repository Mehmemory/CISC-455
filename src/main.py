from solvers.simple import SimpleSolver
from puzzle import Puzzle
from utils import TileType

import copy

MAX_GENERATION = 10
POPULATION_SIZE = 50
MUTATION_RATE = 0.4
INDIVIDUAL_MUTATION_RATE = 0.2
MATING_POOL_SIZE = 7

PUZZLE_DATA = [
    [TileType.SPACE, TileType.SPACE, TileType.WATER, TileType.SPACE, TileType.SPACE, TileType.WATER, TileType.WATER, TileType.WATER],
    [TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE],
    [TileType.WATER, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE],
    [TileType.WATER, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.WATER, TileType.SPACE, TileType.WATER, TileType.SPACE],
    [TileType.WATER, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.WATER, TileType.HORSE, TileType.WATER, TileType.SPACE],
    [TileType.WATER, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE],
    [TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE, TileType.SPACE],
    [TileType.SPACE, TileType.SPACE, TileType.WATER, TileType.SPACE, TileType.SPACE, TileType.WATER, TileType.WATER, TileType.WATER]
]

def main():
    puzzle = Puzzle(8, 8, PUZZLE_DATA, 10)

    solver = SimpleSolver(puzzle, population_size=POPULATION_SIZE, mutation_rate=MUTATION_RATE, individual_mutation_rate=INDIVIDUAL_MUTATION_RATE, mating_pool_size=MATING_POOL_SIZE)

    solver.print_setup()

    solver.initialize_population()

    while solver.generation < MAX_GENERATION:
        solver.run_generation()

        best_solution, best_fitness = solver.best_solution()
        solver.pprint_solution(best_solution)
        print(f"Fitness: {best_fitness}")
        print("-" * 80)


if __name__ == "__main__":
    main()