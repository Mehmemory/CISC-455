import matplotlib.pyplot as plt
import numpy as np

def plot_fitness(avg_fitness, max_fitness, min_fitness, puzzle_name):
	generations = range(len(avg_fitness))

	avg_fitness = np.array(avg_fitness)
	max_fitness = np.array(max_fitness)
	min_fitness = np.array(min_fitness)

	plt.figure()
	plt.plot(generations, avg_fitness)
	plt.plot(generations, max_fitness)
	plt.plot(generations, min_fitness)
	plt.xlabel("Generation")
	plt.ylabel("Fitness")
	plt.title(f"Generation vs Fitness plot ({puzzle_name})")

def plot_strategy(avg_strategy, max_strategy, min_strategy,puzzle_name):
	generations = range(len(avg_strategy))
	n = len(avg_strategy[0])
	m = (n + 1) // 2
	fig, axes = plt.subplots(2, m)

	avg_strategy = np.array(avg_strategy)
	max_strategy = np.array(max_strategy)
	min_strategy = np.array(min_strategy)

	for i in range(m-1):
		axes[0, i].plot(generations, avg_strategy[:, i])
		axes[0, i].plot(generations, max_strategy[:, i])
		axes[0, i].plot(generations, min_strategy[:, i])
		axes[0, i].set_title(f"Strategy parameter {i+1}")
		axes[1, i].plot(generations, avg_strategy[:, m+i])
		axes[1, i].plot(generations, max_strategy[:, m+i])
		axes[1, i].plot(generations, min_strategy[:, m+i])
		axes[1, i].set_title(f"Strategy parameter {m+i+1}")

	if n % 2 != 0:
		axes[0, m-1].plot(generations, avg_strategy[:, n-1])
		axes[0, m-1].plot(generations, max_strategy[:, n-1])
		axes[0, m-1].plot(generations, min_strategy[:, n-1])
		axes[0, m-1].set_title(f"Strategy parameter {n}")

	# Hide x labels and tick labels for top plots and y ticks for right plots.
	for ax in axes.flat:
		ax.set(xlabel="Generation", ylabel="Strategy parameter")
		ax.label_outer()

def plot_statistics(avg_fitness, max_fitness, min_fitness, avg_strategy, max_strategy, min_strategy, puzzle_name):
	plot_fitness(avg_fitness, max_fitness, min_fitness, puzzle_name)
	plot_strategy(avg_strategy, max_strategy, min_strategy, puzzle_name)
	plt.show()