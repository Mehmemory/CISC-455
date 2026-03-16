from enum import Enum
import random

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
class Obj(Enum):
	HORSE = -1
	SPACE = 0
	WATER = 1
	# CHERRY = 2
	# APPLE = 3
	# BEES = 4

	def __str__(self):
		return self.name

class Point:
	def __init__(self, x, y):
		self.x = x
		self.y = y
	
	def __add__(self, other): return Point(self.x + other.x, self.y + other.y)
	def __str__(self): return f"({self.x}, {self.y})"
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
		if tile == "#": r.append(Obj.WATER)
		elif (tile == "O" or tile == "o"):
			assert START_POS is None, "Can't have multiple start positions"
			r.append(Obj.HORSE)
			START_POS = Point(x, y) 
		else:
			r.append(Obj.SPACE)
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
	return pos in placed_walls or get_tile(pos) == Obj.WATER

# Check if this is an exit tile on the edge of the map
def is_exit(x, y=None):
	pos = to_point(x, y)
	return (pos.x == 0 or pos.y == 0 or pos.x == PUZZLE_WIDTH - 1 or pos.y == PUZZLE_HEIGHT - 1) and not is_wall(pos)

# Add/remove wall
def add_wall(x, y=None): placed_walls.add(to_point(x, y))
def remove_wall(x, y=None): placed_walls.remove(to_point(x, y))
def list_walls(): return " ".join(map(str, placed_walls))

# Print the puzzle including placed walls
def print_puzzle():
	puzzle_str = PUZZLE_DATA.copy()
	for p in placed_walls:
		row = puzzle_str[p.y]
		puzzle_str[p.y] = row[: p.x] + "@" + row[p.x + 1 :]
	print("\n".join(puzzle_str))

# =========================== #

# TESTS TO MAKE SURE THIS WORKS
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


# =========================== #

POPULATION_SIZE = 1000
MATING_POOL_SIZE = 750	# allow all but the worst of the worst
MAX_GENERATIONS = 10

population = [] 	# dictionary with { "walls": [], and "fitness": n }
generation = 0
	
	
#  Create a random solution that just picks from random available wall positions
def random_solution():
	random_wall_positions = random.sample(valid_walls, MAX_WALLS)
	return { "walls": random_wall_positions, "fitness": get_fitness(random_wall_positions) }

#	Initialize the population with random solutions
for i in range(POPULATION_SIZE):
	population.append(random_solution())


#	Selection via linear ranking
def tournament():

	# Sort by fitness. First element is the lowest, last element is the highest
	candidates = sorted(population, key = lambda x: x["fitness"])
	
	# Get the weight of each index ([1, 2, 3, 4, 5, ... n-1, n])
	weights = range(1, len(candidates) + 1)

	# Choose a bunch of candidates based on their weight of being picked
	return random.choices(candidates, weights=weights, k=MATING_POOL_SIZE)


#	Temporary
def get_fitness(list_of_walls):
	return 0


# 	Evolve!
while generation < MAX_GENERATIONS:
	generation += 1

	mating_pool = tournament()


	# do crossover, mutation, etc