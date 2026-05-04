import matplotlib.pyplot as plt
import numpy as np

def plot_fitness(avg_fitness, max_fitness, min_fitness, puzzle_name):
	generations = range(len(avg_fitness))

	avg_fitness = np.array(avg_fitness)
	max_fitness = np.array(max_fitness)
	min_fitness = np.array(min_fitness)

	fig = plt.figure()
	plt.plot(generations, avg_fitness, label="Average fitness")
	plt.plot(generations, max_fitness, label="Max fitness")
	plt.plot(generations, min_fitness, label="Min fitness")
	plt.xlabel("Generation")
	plt.ylabel("Fitness")
	fig.suptitle(f"Generation vs Fitness ({puzzle_name})")
	fig.legend()

def plot_statistics(avg_fitness, max_fitness, min_fitness, puzzle_name):
	plot_fitness(avg_fitness, max_fitness, min_fitness, puzzle_name)
	plt.show()