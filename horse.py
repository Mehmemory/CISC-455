from enum import Enum
from collections import deque
import random
import copy
import math
import time
import os

from puzzle_loader import load_puzzle

# Define puzzles in the /puzzles folder
PUZZLE_NAME = "maze"

# =========================== #

PUZZLE_FILE = load_puzzle(PUZZLE_NAME)

PUZZLE_DATA = PUZZLE_FILE["data"]
assert len(PUZZLE_DATA) > 0, "Puzzle is empty"

MAX_WALLS = PUZZLE_FILE["walls"]
OPTIMAL_AREA = PUZZLE_FILE["optimal"]

# =========================== #

# Classes and enums
class TileType(Enum):
	HORSE = -1
	SPACE = 0
	WATER = 1
	CHERRY = 2
	APPLE = 3
	BEES = 4

	def __str__(self):
		return self.name

class Point:
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def __add__(self, other): return Point(self.x + other.x, self.y + other.y)
	def __str__(self): return f"({self.x}, {self.y})"
	def __repr__(self): return self.__str__()
	def __eq__(self, other): return self.x == other.x and self.y == other.y
	def __hash__(self): return hash((self.x, self.y))

	def move(self, x, y):
		self.x += x
		self.y += y
		return self

# =========================== #

# List of Points representing walls placed by the algorithm, should not exceed MAX_WALLS
placed_walls = set()		# walls have been placed here
valid_walls = []			# walls CAN be placed here

# Constants and puzzle creation
PUZZLE = []
PUZZLE_HEIGHT = len(PUZZLE_DATA)
PUZZLE_WIDTH = len(PUZZLE_DATA[0])
START_POS = None

for y, row in enumerate(PUZZLE_DATA):
	assert len(row) == PUZZLE_WIDTH, "Puzzle grid is not rectangular"
	r = []

	for x, tile in enumerate(row):
		lt = tile.lower()

		if tile == "#": r.append(TileType.WATER)
		elif lt == "c": r.append(TileType.CHERRY)
		elif lt == "a": r.append(TileType.APPLE)
		elif lt == "b": r.append(TileType.BEES)

		elif lt == "o":
			assert START_POS is None, "Can't have multiple start positions"
			r.append(TileType.HORSE)
			START_POS = Point(x, y)
		else:
			r.append(TileType.SPACE)
			valid_walls.append(Point(x, y))

	PUZZLE.append(r)

assert START_POS is not None, "No start position provided!"

# =========================== #

# Utility functions
# Allow functions to use either (x, y) or (Point)
def to_point(xOrPos, y=None):
	if isinstance(xOrPos, Point): return xOrPos
	else: return Point(xOrPos, y)

def get_tile(x, y=None):
	pos = to_point(x, y)
	return PUZZLE[pos.y][pos.x]

# Check if a point contains ANY type of wall
def is_wall(x, y=None):
	pos = to_point(x, y)
	return pos in placed_walls or get_tile(pos) == TileType.WATER

# Add/remove wall
def add_wall(x, y=None): placed_walls.add(to_point(x, y))
def remove_wall(x, y=None): placed_walls.remove(to_point(x, y))
def list_walls(): return " ".join(map(str, placed_walls))

# Print the puzzle including placed walls
def print_puzzle(walls=placed_walls):
	puzzle_str = PUZZLE_DATA.copy()
	for p in walls:
		row = puzzle_str[p.y]
		puzzle_str[p.y] = row[: p.x] + "@" + row[p.x + 1 :]
	print("\n".join(puzzle_str))

global total_fitness_calculations
total_fitness_calculations = 0

# =========================== #

# TESTS TO MAKE SURE THIS WORKS
"""
print(f"Puzzle size is {PUZZLE_WIDTH} x {PUZZLE_HEIGHT}")
print(f"Start position is {START_POS}")

add_wall(Point(0, 0))
add_wall(1, 0)
add_wall(0, 1)
add_wall(1, 1)

print(f"(3, 0) is wall: {is_wall(3, 0)}")
print(f"(7, 0) is wall: {is_wall(7, 0)}")
print(f"(1, 1) is wall: {is_wall(1, 1)}")
remove_wall(Point(1, 1))
print(f"(1, 1) is still wall: {is_wall(1, 1)}")

print(f"(1, 1) + (1, 3) = {Point(1, 1) + Point(1, 3)}")
print(f"(1, 1) + (1, 4) = {Point(1, 1).move(1, 4)}")
print(f"Walls: {list_walls()}")
print_puzzle()
"""


# ===========================  FITNESS CALCULATION FUNCTIONS =========================== #

FITNESS_EXPONENT = 2	# scales fitness

def on_edge(pos):
	# returns true if a given pos is on the edge of the puzzle
	return pos.x == 0 or pos.y == 0 or pos.x == PUZZLE_WIDTH-1 or pos.y == PUZZLE_HEIGHT-1

def floodfill(puzzleLayout):
	# returns a 2d array the coorisponds to how many steps it takes to reach each tile of the puzzleLayout
	# -1 means the tile is unreachable:

	results = [[-1 for _ in range(PUZZLE_WIDTH)] for _ in range(PUZZLE_HEIGHT)]	# initialize the array with all -1's
	queue = deque()												# stores which tile to check next
	results[START_POS.y][START_POS.x] = 0
	if not on_edge(START_POS):
		queue.append((START_POS, 0))		# add startpos to the queue and note that it takes 0 steps to get there

	neighbors = [Point(-1,0), Point(1,0), Point(0,-1), Point(0,1)]
	while queue:
		cur = queue.popleft()
		for p in neighbors:	# checks each neighbor around current
			next = cur[0]+p

			# if the tile hasn't been checked yet and it's not water...
			if results[next.y][next.x] == -1 and puzzleLayout[next.y][next.x] != TileType.WATER:
				results[next.y][next.x] = cur[1]+1	# update results
				if not on_edge(next):	# add to queue if its not on the edge
					queue.append((next, cur[1]+1))

	return results

def get_fitness(walls, puzzle, defaultEscapes):

	global total_fitness_calculations
	total_fitness_calculations += 1

	# Calculates fitness based on the number of reachable exits and how long they take to get them compared to a default board
	# If the horse is fully enclosed, adds additional fitness for each tile and item enclosed
	# defaultEscapes is a tuple list with 		[0] = coordinates       and 	[1] = depth

	# create a temporary puzzle layout that counts walls as water (since they function the same)
	fitness = 0
	combinedPuzzle = [row[:] for row in puzzle]
	for w in walls:
		combinedPuzzle[w.y][w.x] = TileType.WATER

	# run floodfill on the board:
	flood = floodfill(combinedPuzzle)

	# Subtract fitness based on how many escapes possible and how long (compared to default) it takes to get to each
	for pos, defaultDepth in defaultEscapes:
		if flood[pos.y][pos.x] == -1:
			fitness+=1
		else:
			diff = flood[pos.y][pos.x] - defaultDepth	# compares depths
			fitness += 1 - (0.5)**(diff)

	# for solutions with no escapes, add the number of enclosed tiles to the fitness:
	enclosed_tiles = 0

	if fitness == len(defaultEscapes):
		for y in range(PUZZLE_HEIGHT):
			for x in range(PUZZLE_WIDTH):	# iterate over each cell
				if flood[y][x] != -1:		# if that cell is enclosed add fitness
					enclosed_tiles+=1
					# add additional fitness for cherries, apples, bees
					if combinedPuzzle[y][x] == TileType.CHERRY:
						enclosed_tiles+=3
					elif combinedPuzzle[y][x] == TileType.APPLE:
						enclosed_tiles+=10
					elif combinedPuzzle[y][x] == TileType.BEES:
						enclosed_tiles-=5

	fitness += enclosed_tiles

	if enclosed_tiles >= OPTIMAL_AREA:
		fitness = math.inf

	return fitness**FITNESS_EXPONENT

# Find default escapes (needed for fitness evaluation):
defaultExits = []
defaultFlood = floodfill(PUZZLE)
for y in range(PUZZLE_HEIGHT):
	for x in range(PUZZLE_WIDTH):
		if on_edge(Point(x,y)) and defaultFlood[y][x] != -1:
			defaultExits.append((Point(x,y), defaultFlood[y][x]))

# ===========================  END OF FITNESS CALCULATION FUNCTIONS =========================== #

#  Create a random solution that just picks from random available wall positions
def random_solution(sigma_init=3.0):
	random_wall_positions = random.sample(valid_walls, MAX_WALLS)
	default_sigmas = [sigma_init for _ in range(MAX_WALLS)]
	return { "walls": random_wall_positions, "sigmas": default_sigmas, "fitness": get_fitness(random_wall_positions, PUZZLE, defaultExits) }


#	Selection via linear ranking (old)
def tournament(population, _):

	# Sort by fitness. First element is the lowest, last element is the highest
	candidates = sorted(population, key = lambda x: x["fitness"])

	# Get the weight of each index ([1, 2, 3, 4, 5, ... n-1, n])
	weights = range(1, len(candidates) + 1)

	# Choose a bunch of candidates based on their weight of being picked
	return random.choices(candidates, weights=weights, k=MATING_POOL_SIZE)

# Roulette selection with linear ranking
def tournament_roulette(population, count):
	mating_pool = []

	candidates = sorted(population, key=lambda x: x["fitness"])

	# We need a lot of offspring for evolution strategy, so instead of working with
	# floating point value, we transform the "roulette markers" to be integers by
	# picking the roulette values in the range [0, rank_sum] where the markers are now
	# just the rank themselves instead of the probability.

	mu = len(population)
	rank_sum = (mu * (mu - 1))/2

	cdf = [0 for i in range(mu)]

	# Compute prefix sum
	for i in range(1, mu):
		cdf[i] = cdf[i-1] + i

	while len(mating_pool) < count:
		roulette_value = random.random() * rank_sum

		i = 0
		while cdf[i] < roulette_value:
			i += 1

		mating_pool.append(candidates[i])

	random.shuffle(mating_pool)

	return mating_pool

# Multi-pointer selection with linear ranking
def tournament_mps(population, count):
	mating_pool = []

	candidates = sorted(population, key=lambda x: x["fitness"])

	# We need a lot of offspring for evolution strategy, so instead of working with
	# floating point value, we transform the "roulette markers" to be integers by
	# picking the roulette values in the range [0, rank_sum] where the markers are now
	# just the rank themselves instead of the probability.

	# For multi-pointer selection, we need to additionally multiply by the lambda
	# because in terms of probability the roulette value is selected in the range [0, 1/lambda]
	# Again, instead of dividing by lambda we can multiplying all the ranks by lambda to achieve
	# the same thing. This works because if lambda is in the range [0, rank_sum], then adding
	# count (count - 1) times to lambda will cover all segments in the interval [0, rank_sum * count].

	mu = len(population)
	rank_sum = (mu * (mu - 1))/2

	cdf = [0 for i in range(mu)]
	cdf[0] = mu * count

	# Compute prefix sum
	for i in range(1, mu):
		cdf[i] = cdf[i-1] + i * count

	i = mu - 2
	roulette_value = cdf[-1] - random.random() * rank_sum
	while len(mating_pool) < count:
		while cdf[i] < roulette_value:
			mating_pool.append(candidates[i])
			roulette_value -= count

		i -= 1

	random.shuffle(mating_pool)

	return mating_pool


# roulette wheel tournament
# def tournament(population, total_fitness):

#     average_fitness = total_fitness / POPULATION_SIZE * 2
#     roulette_value = random.random() * average_fitness
#     pool = []
#     i = 0

#     while len(pool) < POPULATION_SIZE:
#         roulette_value -= population[i]["fitness"]
#         while roulette_value <= 0:
#             roulette_value += average_fitness
#             if len(pool) < POPULATION_SIZE:
#                 pool.append(population[i])
#         i+=1

#     return pool


def mutate(parent, lr, sigma_bounds):
	"""
	Generate a mutated solution using a Gaussian mutation step size and self-adaptation.

	Parameters:
		parent       : (dict) A single solution.
		lr           : (float) learning rate.
		sigma_bounds : (float) Lower and upper boundary for sigma.

	Returns:
		child        : (dict) A new mutated solution.
	"""
	sigma_lb, sigma_ub = sigma_bounds

	parent_sigmas = parent["sigmas"] # Sigma corresponding to the parent
	parent_walls = parent["walls"] # Walls from the parent solution
	filledspaces = set(parent_walls) # set of unique walls to check for duplicates

	child_sigmas = []

	for sigma in parent_sigmas:
		child_sigma = sigma * math.exp(lr * random.gauss(0, 1))
		# Enforce upper and lower bound for child sigma
		if sigma_lb > child_sigma:
			child_sigma = sigma_lb
		if sigma_ub < child_sigma:
			child_sigma = sigma_ub
		child_sigmas.append(child_sigma)

	# occupied_walls = set(parent["walls"])

	child_walls = []

	for wall, child_sigma in zip(parent_walls, child_sigmas):
		mutate_prob = random.random()

		if mutate_prob >= INDIVIDUAL_WALL_MUTATION_RATE:
			child_walls.append(wall)
			continue

		found_valid_pos = False
		new_wall = None
		num_attempts = 0

		while not found_valid_pos and num_attempts < DISPLACEMENT_MAX_ATTEMPTS:
			new_wall = Point(round(wall.x + child_sigma * random.gauss(0, 1)), round(wall.y + child_sigma * random.gauss(0, 1)))

			# Clamp perturbed wall position to be within the grid
			if new_wall.x < 0:
				new_wall.x = 0
			elif new_wall.x >= PUZZLE_WIDTH:
				new_wall.x = PUZZLE_WIDTH - 1
			if new_wall.y < 0:
				new_wall.y = 0
			elif new_wall.y >= PUZZLE_HEIGHT:
				new_wall.y = PUZZLE_HEIGHT - 1

			num_attempts += 1

			if PUZZLE[new_wall.y][new_wall.x] == TileType.SPACE:
				if new_wall not in filledspaces: # make sure new wall position is not occupied
					found_valid_pos = True

		# If no valid position has been found after generating perturbed wall
		# positions DISPLACEMENT_MAX_ATTEMPTS number of times, then give up and
		# keep the current wall position. Otherwise, add the new wall position to
		# child's walls.
		if not found_valid_pos:
			child_walls.append(wall)
		else:
			child_walls.append(new_wall)
			filledspaces.add(new_wall) #add new wall to set so that it is not chosen again for subsequent walls in this mutation
			filledspaces.remove(wall)

		# # Get possible positions for the wall to be moved to
		# possible_positions = []

		# queue = deque()

		# for dir in DIRS:
		# 	new_pos = wall + dir
		# 	if (0 <= new_pos.x < PUZZLE_WIDTH and 0 <= new_pos.y < PUZZLE_HEIGHT):
		# 		queue.append((new_pos, 1))

		# # Perform BFS to discover all admissible wall positions within a circle around the
		# # current wall position with radius == displacement_radius
		# while len(queue) > 0:
		# 	curr_pos, curr_dist = queue.popleft()

		# 	if PUZZLE[curr_pos.y][curr_pos.x] == TileType.SPACE:
		# 		possible_positions.append(curr_pos)

		# 	# If the current dist is equal or greater than the displacement radius, stop further
		# 	# searches
		# 	if curr_dist >= displacement_radius:
		# 		continue

		# 	for dir in DIRS:
		# 		new_pos = curr_pos + dir

		# 		if (0 <= new_pos.x < PUZZLE_WIDTH and 0 <= new_pos.y < PUZZLE_HEIGHT):
		# 			queue.append((new_pos, curr_dist + 1))

		# # If there are no positions the wall can be moved to, keep it where it is
		# if len(possible_positions) == 0:
		# 	new_walls.append(wall)
		# else:
		# 	new_wall = random.choice(possible_positions)
		# 	new_walls.append(new_wall)
		# 	# Remove the old wall's position and add the new wall's position to
		# 	# the occupied walls set so subsequently displaced walls can not
		# 	# choose the same position
		# 	occupied_walls.remove(wall)
		# 	occupied_walls.add(new_wall)

	child = dict(
		sigmas=child_sigmas,
		walls=child_walls,
	)

	return child


def crossover(parent1, parent2):
	# combine walls from 2 parents
	# for simplicity of having any crossover function, just take half of the walls from one parent and half from the other, but make sure they are unique and valid placements
	# will skip if location already in the solution and find a different wall from the other parent to add instead
	point = random.randint(1, MAX_WALLS//2 - 1)
	# give it a chance to be more weighted towards lower values.
	point = random.randint(1, point)
	point = random.randint(1, point)
	start = random.randint(0, MAX_WALLS-1)

	starter = set(parent1["walls"]).intersection(set(parent2["walls"]))

	# since sets are unordered, we will just take the first point walls from parent 1 and the rest from parent 2
	child_a_walls = set(starter)
	child_b_walls = set(starter)

	# cross walls
	#cross point number of walls from one parent into another
	i = start
	added = 0
	while len(child_a_walls) < MAX_WALLS and added < point:
		if parent1["walls"][i % MAX_WALLS] not in child_a_walls:
			child_a_walls.add(parent1["walls"][i % MAX_WALLS])
			added += 1
		i+=1
	i = start
	added = 0
	while len(child_b_walls) < MAX_WALLS and added < point:
		if parent2["walls"][i % MAX_WALLS] not in child_b_walls:
			child_b_walls.add(parent2["walls"][i % MAX_WALLS])
			added += 1
		i+=1

	# that should hopefully mean there are point number of walls from parent 1
	#fill in the rest with unique placements from the other parent
	i = start
	while len(child_a_walls) < MAX_WALLS:
		if parent2["walls"][i % MAX_WALLS] not in child_a_walls:
			child_a_walls.add(parent2["walls"][i % MAX_WALLS])
		i+=1
	i=start
	while len(child_b_walls) < MAX_WALLS:
		if parent1["walls"][i % MAX_WALLS] not in child_b_walls:
			child_b_walls.add(parent1["walls"][i % MAX_WALLS])
		i+=1

	# cross sigmas
	# maps wall to corrisponding sigma, so can find the sigma using the wall (so we only have to look at the walls to detemrine sigma)
	parent1_map = {w: s for w, s in zip(parent1["walls"], parent1["sigmas"])}
	parent2_map = {w: s for w, s in zip(parent2["walls"], parent2["sigmas"])}

	sigma_a = []
	for w in child_a_walls:
		if w in parent1_map and w in parent2_map:
		# combine sigmas of walls in both parents
			sigma_a.append((parent1_map[w] + parent2_map[w]) / 2)
		elif w in parent1_map:
			# if it was from parent 1 only, take that sigma
			sigma_a.append(parent1_map[w])
		else:
			# if it was from parent 2 only, take that sigma
			sigma_a.append(parent2_map[w])

	# same thing but for child b
	sigma_b = []
	for w in child_b_walls:
		if w in parent1_map and w in parent2_map:
			sigma_b.append((parent1_map[w] + parent2_map[w]) / 2)
		elif w in parent2_map:
			sigma_b.append(parent2_map[w])
		else:
			sigma_b.append(parent1_map[w])

	# return walls and sigmas
	return { "walls": list(child_a_walls), "sigmas": sigma_a }, { "walls": list(child_b_walls), "sigmas": sigma_b }



POPULATION_SIZE = 250
MATING_POOL_SIZE = POPULATION_SIZE // 2
MAX_GENERATIONS = 250
DISPLACEMENT_MAX_ATTEMPTS = 5 # maximum number of attempts to before giving up moving a wall in mutation
SOLUTION_MUTATION_RATE = 0.3 # probablity for a solution to undergo mutation
INDIVIDUAL_WALL_MUTATION_RATE = 0.4 # probablity for an individual wall to change its position
SIGMA_INIT = 3.5 # initial value for sigma for each wall

DIRS = [Point(-1, 0), Point(1, 0), Point(0, -1), Point(0, 1)]



def main():
	print("\n-> Initializing with population of", POPULATION_SIZE)

	population = [random_solution(sigma_init=SIGMA_INIT) for _ in range(POPULATION_SIZE)] 	# dictionary with { "walls": [], and "fitness": n }
	offspring_size = 7 * POPULATION_SIZE
	generation = 0
	sigma_bounds = (1, max(PUZZLE_WIDTH, PUZZLE_HEIGHT) // 2)
	learning_rate = 1 / math.sqrt(MAX_WALLS)
	best_solution = { "generation": -1, "fitness": 0 }   # highest fitness so far
	global_start_time = time.perf_counter()

	if os.path.exists("last_run.csv"):
		os.remove("last_run.csv")

	csv = open("last_run.csv", "a", encoding="utf-8")
	csv.write("Generation, Avg Fitness, Best Fitness, Max Fitness Overall\n")

	global total_fitness_calculations

	# 	Evolve!
	while generation < MAX_GENERATIONS:

		# Process previous generation

		start_time = time.perf_counter()

		offspring = []

		# check for best solution so far + stats from previous generation
		best = best_solution["fitness"]
		avg_fitness = 0
		best_in_generation = { "fitness": 0 }
		avg_strategy = [0 for i in range(MAX_WALLS)]
		max_strategy = [float('-inf') for i in range(MAX_WALLS)]
		min_strategy = [float('inf') for i in range(MAX_WALLS)]

		for p in population:
			fit = p["fitness"]

			avg_fitness += fit
			if fit > best_in_generation["fitness"]: best_in_generation = p

			for i, v in enumerate(p["sigmas"]):
				avg_strategy[i] += v
				if v > max_strategy[i]:
					max_strategy[i] = v

				if v < min_strategy[i]:
					min_strategy[i] = v

			if best_solution["generation"] == -1 or fit > best:
				best_solution = copy.deepcopy(p)
				best_solution["generation"] = generation
				new_best = best_solution["fitness"]
				print(f"	-> Found a better solution! ({best} -> {new_best})")
				best = new_best

		for i in range(MAX_WALLS):
			avg_strategy[i] = avg_strategy[i] / len(population)

		avg_fitness /= len(population)

		print("-> Max strategy / wall:", [round(x, 3) for x in max_strategy])
		print("-> Min strategy / wall:", [round(x, 3) for x in min_strategy])
		print("-> Avg strategy / wall:", [round(x, 3) for x in avg_strategy])
		print("->  Avg fitness for gen was", avg_fitness)
		print("-> Best fitness for gen was", best_in_generation["fitness"])
		# print_puzzle(best_in_generation["walls"])

		# Write to file
		csv.write(f"{generation},{avg_fitness: .4f},{best_in_generation['fitness']},{best}\n")
		csv.flush()

		if best >= math.inf:
			print(f"-> !!! FOUND OPTIMAL SOLUTION !!!")
			break


		# Start next generation

		generation += 1

		print("\n-> Starting generation", generation)
		print("-> Population size:", len(population))
		print(f"-> Best fitness so far is {best_solution['fitness']} (from gen {best_solution['generation']})")
		print("-> Fitness calculations:", total_fitness_calculations)

		# mating_pool = tournament(population, best_solution["fitness"])
		mating_pool = tournament_roulette(population, offspring_size)

		# run crossover until mating pool is empty
		while len(mating_pool) > 2:
			# pop two random values from the mating pool
			p1 = mating_pool.pop()
			p2 = mating_pool.pop()

			# run crossover on them
			offspring1, offspring2 = crossover(p1, p2)

			# mutate and add to offspring list
			if random.random() < SOLUTION_MUTATION_RATE:
				offspring1 = mutate(offspring1, learning_rate, sigma_bounds)

			if random.random() < SOLUTION_MUTATION_RATE:
				offspring2 = mutate(offspring2, learning_rate, sigma_bounds)

			# calculate fitness of offsprings
			offspring1["fitness"] = get_fitness(offspring1["walls"], PUZZLE, defaultExits)
			offspring2["fitness"] = get_fitness(offspring2["walls"], PUZZLE, defaultExits)

			offspring.append(offspring1)
			offspring.append(offspring2)
			# offspring.append(p1)
			# offspring.append(p2)

		offspring.sort(key=lambda s: s["fitness"], reverse=True)

		population = offspring[:POPULATION_SIZE]

		end_time = time.perf_counter()

		print(f"-> Generation took {(end_time - start_time) * 1000.0: .3f} ms")


	population = sorted(population, key = lambda x: x["fitness"], reverse=True)
	# fitnesses = list(map(lambda x: x["fitness"], population))

	print("===========================")

	print("Total fitness calculations:", total_fitness_calculations)
	# print("\nWorst Solution:")
	# print_puzzle(population[-1]["walls"])
	# print(f"Fitness: {population[-1]['fitness']}")

	print("\nBest Solution from Last Generation:")
	print_puzzle(population[0]["walls"])
	print(f"Fitness: {population[0]['fitness']}")

	print(f"\nBest Solution overall: (from gen {best_solution['generation']})")
	print_puzzle(best_solution["walls"])
	print(f"Fitness: {best_solution['fitness']}")

	print(f"\nPopulation size: {len(population)}")
	print(f"Generations: {generation}")
	print(f"Time elapsed: {time.perf_counter() - global_start_time: .6f} secs")
	print("===========================")


	# Store last run in csv
	csv.close()
	print("Saved to list_run.csv")


if __name__ == '__main__':
	main()
