from enum import Enum
from collections import deque
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


# ===========================  FITNESS CALCULATION FUNCTIONS =========================== #

def on_edge(pos):
	# returns true if a given pos is on the edge of the puzzle
	return pos.x == 0 or pos.y == 0 or pos.x == PUZZLE_WIDTH-1 or pos.y == PUZZLE_HEIGHT-1

def floodfill(puzzleLayout):
	# returns a 2d array the coorisponds to how many steps it takes to reach each tile of the puzzleLayout
	# -1 means the tile is unreachable:

	results = [[-1 for _ in range(PUZZLE_HEIGHT)] for _ in range(PUZZLE_WIDTH)]	# initialize the array with all -1's
	queue = deque()												# stores which tile to check next
	results[START_POS.x][START_POS.y] = 0	
	if not on_edge(START_POS):
		queue.append((START_POS, 0))		# add startpos to the queue and note that it takes 0 steps to get there

	neighbors = [Point(-1,0), Point(1,0), Point(0,-1), Point(0,1)]
	while queue:
		cur = queue.popleft()
		for p in neighbors:	# checks each neighbor around current
			next = cur[0]+p

			# if the tile hasn't been checked yet and it's not water...
			if results[next.x][next.y] == -1 and puzzleLayout[next.x][next.y] != Obj.WATER:

				results[next.x][next.y] = cur[1]+1	# update results
				if not on_edge(next):	# add to queue if its not on the edge
					queue.append((next, cur[1]+1))

	return results

def get_fitness(walls, puzzle, defaultEscapes):
	# Calculates fitness based on the number of reachable exits and how long they take to get them compared to a default board
	# If the horse is fully enclosed, adds additional fitness for each tile and item enclosed
	# defaultEscapes is a tuple list with 		[0] = coordinates       and 	[1] = depth

	# create a temporary puzzle layout that counts walls as water (since they function the same)
	combinedPuzzle = puzzle
	for i in walls:
		combinedPuzzle[walls[i].x][walls[i].y] = 1
	
	# run floodfill on the board:
	flood = floodfill(combinedPuzzle)
	
	# Subtract fitness based on how many escapes possible and how long (compared to default) it takes to get to each
	for i in defaultEscapes:
		pos, defaultDepth = defaultEscapes[i]
		if flood[pos.x][pos.y] == -1:
			fitness+=1
		else:
			diff = flood[pos.x][pos.y] - defaultDepth	# compares depths
			fitness += 1 - (0.5)**(diff)
	
	# for solutions with no escapes, add the number of enclosed tiles to the fitness:
	if fitness == len(defaultEscapes):
		for x in range(PUZZLE_WIDTH):
			for y in range(PUZZLE_HEIGHT):	# iterate over each cell
				if flood[x][y] != 0:		# if that cell is enclosed add fitness
					fitness+=1
					# add additional fitness for cherries, apples, bees
					if combinedPuzzle[x][y] == Obj.CHERRY:
						fitness+=3
					elif combinedPuzzle[x][y] == Obj.APPLE:
						fitness+=10
					elif combinedPuzzle[x][y] == Obj.BEES:
						fitness-=5

	return fitness**FITNESS_EXPONENT

# ===========================  END OF FITNESS CALCULATION FUNCTIONS =========================== #

POPULATION_SIZE = 1000
MATING_POOL_SIZE = 750	# allow all but the worst of the worst
MAX_GENERATIONS = 10
FITNESS_EXPONENT = 2	# scales fitness

# Find default escapes (needed for fitness evaluation):
defaultExits = []
defaultFlood = floodfill(PUZZLE_DATA)
for x in range(PUZZLE_WIDTH):
	for y in range(PUZZLE_HEIGHT):
		if on_edge(Point(x,y)):
			defaultExits.append((Point(x,y), defaultFlood[x][y]))

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


# 	Evolve!
while generation < MAX_GENERATIONS:
	generation += 1

	mating_pool = tournament()


	# do crossover, mutation, etc