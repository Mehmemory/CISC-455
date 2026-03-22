from enum import Enum
from collections import deque
import random
import copy
import math

# Define the puzzle here
# Wall is #, Space is -, Start pos is O

PUZZLE_DATA = [
	'--####--',
	'--------',
	'#------#',
	'--------',
	'---##---',
	'#---O--#',
	'#--##--#',
	'#------#'
]
MAX_WALLS = 10

assert len(PUZZLE_DATA) > 0, "Puzzle is empty"

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
		if tile == "#": r.append(TileType.WATER)
		elif (tile == "O" or tile == "o"):
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

FITNESS_EXPONENT = 1	# scales fitness

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
	if fitness == len(defaultEscapes):
		for y in range(PUZZLE_HEIGHT):
			for x in range(PUZZLE_WIDTH):	# iterate over each cell
				if flood[y][x] != -1:		# if that cell is enclosed add fitness
					fitness+=1
					# add additional fitness for cherries, apples, bees
					if combinedPuzzle[y][x] == TileType.CHERRY:
						fitness+=3
					elif combinedPuzzle[y][x] == TileType.APPLE:
						fitness+=10
					elif combinedPuzzle[y][x] == TileType.BEES:
						fitness-=5

	return fitness**FITNESS_EXPONENT

# Find default escapes (needed for fitness evaluation):
defaultExits = []
defaultFlood = floodfill(PUZZLE)
for y in range(PUZZLE_HEIGHT):
	for x in range(PUZZLE_WIDTH):
		if on_edge(Point(x,y)) and defaultFlood[y][x] != -1:
			defaultExits.append((Point(x,y), defaultFlood[y][x]))

def test_fitness():
	print("\n===== FITNESS FUNCTION TESTS =====\n")
	no_walls = []
	f0 = get_fitness(no_walls, copy.deepcopy(PUZZLE), defaultExits)
	print("Test 1: No walls")
	print_puzzle(no_walls)
	print(f"Fitness: {f0}\n")

	# 2. Random walls
	random_walls = random.sample(valid_walls, MAX_WALLS)
	f1 = get_fitness(random_walls, copy.deepcopy(PUZZLE), defaultExits)
	print("Test 2: Random walls")
	print_puzzle(random_walls)
	print(f"Fitness: {f1}\n")

	# 3. Try to block the start position (surround it)
	blocking_walls = []
	for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
		p = Point(START_POS.x + dx, START_POS.y + dy)
		if p in valid_walls:
			blocking_walls.append(p)

	f2 = get_fitness(blocking_walls, copy.deepcopy(PUZZLE), defaultExits)
	print("Test 3: Block around start")
	print_puzzle(blocking_walls)
	print(f"Fitness: {f2}\n")

	# 4. Manual wall placements
	blocking_walls = []
	for x, y in [(1,0),(0,1),(6,0),(7,1),(7,3),(7,4),(6,6),(5,6),(2,6),(1,6),(0,3),(0,4)]:
		p = Point(x, y)
		if p in valid_walls:
			blocking_walls.append(p)

	f2 = get_fitness(blocking_walls, copy.deepcopy(PUZZLE), defaultExits)
	print("Test 4: Manual wall placements")
	print_puzzle(blocking_walls)
	print(f"Fitness: {f2}\n")

	# 5. Repeat same input (consistency check)
	f_repeat = get_fitness(random_walls, copy.deepcopy(PUZZLE), defaultExits)
	print("Test 5: Consistency check")
	print(f"First: {f1}, Second: {f_repeat}")
	print("Same result?" , f1 == f_repeat)

	print("\n===== END TESTS =====\n")
#test_fitness()
# ===========================  END OF FITNESS CALCULATION FUNCTIONS =========================== #

#  Create a random solution that just picks from random available wall positions
def random_solution(sigma_init=3.0):
	random_wall_positions = random.sample(valid_walls, MAX_WALLS)
	default_sigmas = [sigma_init for _ in range(MAX_WALLS)]
	return { "walls": random_wall_positions, "sigmas": default_sigmas, "fitness": get_fitness(random_wall_positions, PUZZLE, defaultExits) }


#	Selection via linear ranking
def tournament(population):

	# Sort by fitness. First element is the lowest, last element is the highest
	candidates = sorted(population, key = lambda x: x["fitness"])

	# Get the weight of each index ([1, 2, 3, 4, 5, ... n-1, n])
	weights = range(1, len(candidates) + 1)

	# Choose a bunch of candidates based on their weight of being picked
	return random.choices(candidates, weights=weights, k=MATING_POOL_SIZE)


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
				found_valid_pos = True

		# If no valid position has been found after generating perturbed wall
		# positions DISPLACEMENT_MAX_ATTEMPTS number of times, then give up and
		# keep the current wall position. Otherwise, add the new wall position to
		# child's walls.
		if not found_valid_pos:
			child_walls.append(wall)
		else:
			child_walls.append(new_wall)

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

	child = dict(sigmas=child_sigmas, walls=child_walls, fitness=get_fitness(child_walls, PUZZLE, defaultExits))

	return child


def crossover(parent1, parent2):
	# combine walls from 2 parents
	# for simplicity of having any crossover function, just take half of the walls from one parent and half from the other, but make sure they are unique and valid placements
	# will skip if location already in the solution and find a different wall from the other parent to add instead
	point = random.randint(1, MAX_WALLS//2 - 1)
	# give it a chance to be more weighted towards lower values.
	point = random.randint(1, point)
	point = random.randint(1, point)

	starter = set(parent1["walls"]).intersection(set(parent2["walls"]))

	# since sets are unordered, we will just take the first point walls from parent 1 and the rest from parent 2
	child_a_walls = set(starter)
	child_b_walls = set(starter)
	i = 0
	while len(child_a_walls) < MAX_WALLS and i < point:
		if parent1["walls"][i] not in child_a_walls:
			child_a_walls.add(parent1["walls"][i])
		i+=1
	i = 0
	while len(child_b_walls) < MAX_WALLS and i < point:
		if parent2["walls"][i] not in child_b_walls:
			child_b_walls.add(parent2["walls"][i])
		i+=1

	# that should hopefully mean there are point number of walls from parent 1
	#fill in the rest with unique placements from the other parent
	i = 0
	while len(child_a_walls) < MAX_WALLS:
		if parent2["walls"][i] not in child_a_walls:
			child_a_walls.add(parent2["walls"][i])
		i+=1
	i=0
	while len(child_b_walls) < MAX_WALLS:
		if parent1["walls"][i] not in child_b_walls:
			child_b_walls.add(parent1["walls"][i])
		i+=1

	# todo: cross these over properly
	sigma_a = parent1["sigmas"]
	sigma_b = parent2["sigmas"]
	
	return { "walls": child_a_walls, "sigmas": sigma_a }, { "walls": child_b_walls, "sigmas": sigma_b }



POPULATION_SIZE = 100
MATING_POOL_SIZE = 20
MAX_GENERATIONS = 5
DISPLACEMENT_MAX_ATTEMPTS = 10 # maximum number of attempts to before giving up moving a wall in mutation
SOLUTION_MUTATION_RATE = 0.2 # probablity for a solution to undergo mutation
INDIVIDUAL_WALL_MUTATION_RATE = 0.2 # probablity for an individual wall to change its position

DIRS = [Point(-1, 0), Point(1, 0), Point(0, -1), Point(0, 1)]



def main():
	
	population = [random_solution() for _ in range(POPULATION_SIZE)] 	# dictionary with { "walls": [], and "fitness": n }
	generation = 0
	sigma_bounds = (1, max(PUZZLE_WIDTH, PUZZLE_HEIGHT) // 2)
	learning_rate = 1 / math.sqrt(MAX_WALLS)
	total_fitness_calculations = POPULATION_SIZE
	best_solution = None   # highest fitness so far

	# 	Evolve!
	while generation < MAX_GENERATIONS:
		generation += 1

		offspring = []
		
		# check for best solution so far
		for p in population:
			if best_solution is None or p["fitness"] > best_solution["fitness"]:
				best_solution = copy.deepcopy(p)

		print("-> Starting generation", generation, "\n-> Best fitness so far is", best_solution["fitness"], "\n-> Fitness calculations: ", total_fitness_calculations)

		mating_pool = tournament(population)

		# run crossover until mating pool is empty
		while len(mating_pool) > 0:
			# pop two random values from the mating pool
			p1 = mating_pool.pop(random.randint(0, len(mating_pool) - 1))
			p2 = mating_pool.pop(random.randint(0, len(mating_pool) - 1))

			# run crossover on them
			cross = crossover(p1, p2)
			
			# mutate and add to offspring list
			offspring.append(mutate(cross[0], learning_rate, sigma_bounds))
			offspring.append(mutate(cross[1], learning_rate, sigma_bounds))
			total_fitness_calculations += 2

		population = offspring


	population = sorted(population, key = lambda x: x["fitness"], reverse=True)
	fitnesses = list(map(lambda x: x["fitness"], population))

	print("===========================")
	print("Total fitness calculations:", total_fitness_calculations)
	print("\nWorst Solution:")
	print_puzzle(population[-1]["walls"])
	print(f"Fitness: {population[-1]['fitness']}")
	print("\nBest Solution:")
	print_puzzle(population[0]["walls"])
	print(f"Fitness: {population[0]['fitness']}")
	print("===========================")


if __name__ == '__main__':
	main()
