from enum import Enum
from collections import deque
import random
import copy
import math
import time

from puzzle_loader import load_puzzle

from plot_stats import plot_statistics

# Define puzzles in the /puzzles folder
PUZZLE_NAME = "day119"

# =========================== #

SHOW_PLOTS = True
PUZZLE_FILE = load_puzzle(PUZZLE_NAME)
PUZZLE_DATA = PUZZLE_FILE["data"]
assert len(PUZZLE_DATA) > 0, "Puzzle is empty"
MAX_WALLS = PUZZLE_FILE["walls"]
OPTIMAL_AREA = PUZZLE_FILE["optimal"]

# ============ PARAMETERS ============ #
POPULATION_SIZE = 450
MATING_POOL_SIZE = POPULATION_SIZE//3
MAX_GENERATIONS = 600
SOLUTION_MUTATION_RATE = 0.15 # probablity for a solution to undergo mutation
INDIVIDUAL_WALL_MUTATION_RATE = 1/MAX_WALLS # probablity for an individual wall to change its position
USELESS_WALL_MUTATION_RATE = 0.8

# =========================== #

# Classes and enums
class TileType(Enum):
	HORSE = -1
	SPACE = 0
	WATER = 1
	CHERRY = 2
	APPLE = 3
	BEES = 4
	PORTAL = 5

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
PORTALS = [[] for _ in range(10)] # 10 portal slots (digits from 0-9)
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
		elif lt.isdigit():		# digit means portal
			r.append(TileType.PORTAL)
			portalID = int(lt)	# digit corresponds to portal id
			PORTALS[portalID].append(Point(x,y))
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

# ===========================  FITNESS CALCULATION FUNCTIONS =========================== #

DIRS = [Point(-1, 0), Point(1, 0), Point(0, -1), Point(0, 1)]

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

	while queue:
		cur = queue.popleft()
		for p in DIRS:	# checks each neighbor around current
			next = cur[0]+p

			# if the tile hasn't been checked yet and it's not water...
			if results[next.y][next.x] == -1 and puzzleLayout[next.y][next.x] != TileType.WATER:
				results[next.y][next.x] = cur[1]+1	# update results
				if not on_edge(next):	# add to queue if its not on the edge
					queue.append((next, cur[1]+1))
				if puzzleLayout[next.y][next.x] == TileType.PORTAL:	# portals
					id = int(PUZZLE_DATA[next.y][next.x])
					for p in PORTALS[id]:	# add all linked portals to the queue
						if results[p.y][p.x] == -1:
							results[p.y][p.x] = cur[1]+1
							if not on_edge(p):
								queue.append((p, cur[1]+1))

	return results

def get_fitness(walls):

	global total_fitness_calculations
	total_fitness_calculations += 1

	# Calculates fitness based on the number of reachable exits and how long they take to get them compared to a default board
	# If the horse is fully enclosed, adds additional fitness for each tile and item enclosed
	# defaultEscapes is a tuple list with 		[0] = coordinates       and 	[1] = depth

	# create a temporary puzzle layout that counts walls as water (since they function the same)
	fitness = len(defaultExits) * -1
	combinedPuzzle = [row[:] for row in PUZZLE]
	for w in walls:
		combinedPuzzle[w.y][w.x] = TileType.WATER

	# run floodfill on the board:
	flood = floodfill(combinedPuzzle)

	# Subtract fitness based on how many escapes possible and how long (compared to default) it takes to get to each
	for pos, defaultDepth in defaultExits:
		if flood[pos.y][pos.x] == -1:
			fitness+=1
		else:
			diff = flood[pos.y][pos.x] - defaultDepth	# compares depths
			fitness += 1 - (0.5)**(diff)

	# for solutions with no escapes, add the number of enclosed tiles to the fitness:
	useless_walls = [0]*MAX_WALLS
	if fitness == 0:

		# add score from enclosed tiles + items
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
	

		# Find useful walls by checking to see if it's next to an enclosed tile:
		i = 0
		for w in walls:
			useful = False
			for d in DIRS:
				neighbor = w+d

				if neighbor.x >= 0 and neighbor.x < PUZZLE_WIDTH and neighbor.y >= 0 and neighbor.y < PUZZLE_HEIGHT: 
					if flood[neighbor.y][neighbor.x] >= 0:
						useful = True
						break
			if not useful:
				useless_walls[i] = 1
			i+=1
	
	else:	# If not enclosed, -100 fitness to prevent negative score enclosed solutions being coutned as worse
		fitness -= 100
	if fitness >= OPTIMAL_AREA:
		fitness = math.inf

	return fitness, useless_walls

# Find default escapes (needed for fitness evaluation):
defaultExits = []
defaultFlood = floodfill(PUZZLE)
for y in range(PUZZLE_HEIGHT):
	for x in range(PUZZLE_WIDTH):
		if on_edge(Point(x,y)) and defaultFlood[y][x] != -1:
			defaultExits.append((Point(x,y), defaultFlood[y][x]))

# ===========================  END OF FITNESS CALCULATION FUNCTIONS =========================== #

#  Create a random solution that just picks from random available wall positions
def random_solution():
	random_wall_positions = random.sample(valid_walls, MAX_WALLS)
	fitness, uw = get_fitness(random_wall_positions)
	return { "walls": random_wall_positions, "fitness": fitness, "useless_walls": uw}

#	Selection via linear ranking
def tournament(population):
	# Sort by fitness. First element is the lowest, last element is the highest
	candidates = sorted(population, key = lambda x: x["fitness"])
	# Get the weight of each index ([1, 2, 3, 4, 5, ... n-1, n])
	weights = range(1, len(candidates) + 1)
	# Choose a bunch of candidates based on their weight of being picked
	return random.choices(candidates, weights=weights, k=MATING_POOL_SIZE)

# ============= MUTATION =================== #
def mutate(parent):
	"""
	Every wall has a chance to mutate, 'useless' walls have a higher chance to mutate
	mutations can be 1 of 3 kinds:
		1) mutate to any random open tile
		2) mutate to a random open tile within 2x2 if the wall
		3) mutate adjacent to another random wall
	"""
	parent_walls = parent["walls"] # Walls from the parent solution
	useless_walls = parent["useless_walls"]
	filledspaces = set(parent_walls) # set of unique walls to check for duplicates

	child_walls = []
	i = -1

	for wall in parent_walls:
		mutate_prob = random.random()
		i+=1
		# Useless walls have higher chance to mutate:
		if mutate_prob >= INDIVIDUAL_WALL_MUTATION_RATE or useless_walls[i] == 1 and mutate_prob >= USELESS_WALL_MUTATION_RATE:
			child_walls.append(wall)
			continue

		# Chose mutation kind:
		mutation_kind = 3
		m1_odds = 0.33
		m2_odds = 0.33
		r = random.random()
		if r < m1_odds:
			mutation_kind = 1
		elif r < m1_odds + m2_odds:
			mutation_kind = 2

		fails = 0
		# MUTATION 1: (random spot)
		if mutation_kind == 1:
			while fails < 10:
				attempt = random.choice(valid_walls)
				if attempt not in filledspaces:
					child_walls.append(attempt)
					filledspaces.remove(wall)
					filledspaces.add(attempt)
					break
				else: 
					fails += 1
					if fails >= 10:
						child_walls.append(wall)

		# MUTATION 2: (2x2 radius)
		elif mutation_kind == 2:
			while fails < 10:
				x_offset = random.randint(-2, 2)
				y_offset = random.randint(-2, 2)
				attempt = wall + Point(x_offset, y_offset)
				# if out of bounds, make the offset work in the opposite direction
				if attempt.x < 0 or attempt.x >= PUZZLE_WIDTH: 
					attempt.x += x_offset*(-2)
				if attempt.y < 0 or attempt.y >= PUZZLE_HEIGHT: 
					attempt.y += y_offset*(-2)

				if attempt not in filledspaces and PUZZLE[attempt.y][attempt.x] == TileType.SPACE:
					child_walls.append(attempt)
					filledspaces.remove(wall)
					filledspaces.add(attempt)
					break
				else: 
					fails += 1
					if fails >= 10:
						child_walls.append(wall)


		# MUTATION 3: (adjacent to other wall)
		else:
			neighbors = [Point(-1,0), Point(1,0), Point(0,-1), Point(0,1), Point(-1,1), Point(1,1), Point(1,-1), Point(-1,-1)]
			random.shuffle(neighbors)
			filledspaces.remove(wall)	# prevents the wall from moving adjacent to itself
			current_walls = list(filledspaces)
			random.shuffle(current_walls)

			found = False
			for w in current_walls:	# choose a random wall
				for n in neighbors:	# choose a random neighbor for that wall
					attempt = w+n
					# check if its a valid position (in bounds + no occupied + free space)
					if attempt.x >= 0 and attempt.x < PUZZLE_WIDTH and attempt.y >= 0 and attempt.y < PUZZLE_HEIGHT: 
						if attempt not in filledspaces and PUZZLE[attempt.y][attempt.x] == TileType.SPACE:
							child_walls.append(attempt)
							filledspaces.add(attempt)
							found = True
							break
				if found: break
			if not found:
				child_walls.append(wall)
				filledspaces.add(wall)

	child = dict(
		walls=child_walls
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

	uw = [0]*MAX_WALLS
	return { "walls": list(child_a_walls), "useless_walls": uw}, { "walls": list(child_b_walls), "useless_walls": uw}


def main():
	print("\n-> Initializing with population of", POPULATION_SIZE)

	population = [random_solution() for _ in range(POPULATION_SIZE)] 	# dictionary with { "walls": [], and "fitness": n }
	generation = 0
	best_solution = { "generation": -1, "fitness": 0 }   # highest fitness so far
	global_start_time = time.perf_counter()

	csv = open("last_run.csv", "w", encoding="utf-8")
	csv.write("Generation, Avg Fitness, Best Fitness, Max Fitness Overall\n")

	global total_fitness_calculations

	avg_fitness = []
	max_fitness = []
	min_fitness = []

	# 	Evolve!
	while generation < MAX_GENERATIONS:

		# Process previous generation

		offspring = []

		avg_fitness.append(0)
		max_fitness.append(float('-inf'))
		min_fitness.append(float('inf'))

		# check for best solution so far + stats from previous generation
		best = best_solution["fitness"]

		for p in population:
			fit = p["fitness"]

			if fit > max_fitness[-1]:
				max_fitness[-1] = fit
			if fit < min_fitness[-1]:
				min_fitness[-1] = fit

			avg_fitness[-1] += fit

			if best_solution["generation"] == -1 or fit > best:
				best_solution = copy.deepcopy(p)
				best_solution["generation"] = generation
				new_best = best_solution["fitness"]
				print(f"	-> Found a better solution! ({best} -> {new_best})")
				best = new_best
				print_puzzle(best_solution["walls"])

		avg_fitness[-1] /= len(population)

		print(f"->  Avg fitness for gen was {avg_fitness[-1]:.4f}")

		# Write to file
		csv.write(f"{generation},{avg_fitness[-1]: .4f},{best_solution['fitness']},{best}\n")
		csv.flush()

		if best >= math.inf:
			print(f"-> !!! FOUND OPTIMAL SOLUTION !!!")
			break

		# Start next generation

		generation += 1

		print("\n-> Starting generation", generation)
		print(f"-> Best fitness so far is {best_solution['fitness']} (from gen {best_solution['generation']})")
		print("-> Fitness calculations:", total_fitness_calculations)

		mating_pool = tournament(population)

		# run crossover until mating pool is empty
		while len(mating_pool) > 2:
			# pop two random values from the mating pool
			p1 = mating_pool.pop()
			p2 = mating_pool.pop()

			# run crossover on them
			offspring1, offspring2 = crossover(p1, p2)

			# mutate and add to offspring list
			m1 = mutate(p1)
			m2 = mutate(p2)
			if random.random() < SOLUTION_MUTATION_RATE:
				offspring1 = mutate(offspring1)

			if random.random() < SOLUTION_MUTATION_RATE:
				offspring2 = mutate(offspring2)

			# calculate fitness of offsprings
			offspring1["fitness"], offspring1["useless_walls"] = get_fitness(offspring1["walls"])
			offspring2["fitness"], offspring2["useless_walls"] = get_fitness(offspring2["walls"])
			m1["fitness"], m1["useless_walls"] = get_fitness(m1["walls"])
			m2["fitness"], m2["useless_walls"] = get_fitness(m2["walls"])

			offspring.append(offspring1)
			offspring.append(offspring2)
			offspring.append(p1)
			offspring.append(p2)
			offspring.append(m1)
			offspring.append(m2)

		offspring.append(best_solution)	# add a copy of best solution to each generation (Elitism)

		population = offspring[:POPULATION_SIZE]


	population = sorted(population, key = lambda x: x["fitness"], reverse=True)

	print("===========================")
	print("Total fitness calculations:", total_fitness_calculations)
	print(f"\nBest Solution overall: (from gen {best_solution['generation']})")
	print_puzzle(best_solution["walls"])
	print(f"Fitness: {best_solution['fitness']}")
	print(f"\nPopulation size: {len(population)}")
	print(f"Generations: {generation}")
	print(f"Time elapsed: {time.perf_counter() - global_start_time: .6f} secs")
	print(f"For {MAX_WALLS} walls, wall mutation rate was: {INDIVIDUAL_WALL_MUTATION_RATE}")
	print("===========================")

	# Store last run in csv
	csv.close()
	print("Saved to list_run.csv")

	if SHOW_PLOTS:
		# Plot statistics
		plot_statistics(
			avg_fitness=avg_fitness,
			max_fitness=max_fitness,
			min_fitness=min_fitness,
			puzzle_name=PUZZLE_NAME
		)

if __name__ == '__main__':
	main()
