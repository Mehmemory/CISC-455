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


def plot_strategy(avg_strategy, max_strategy, min_strategy,puzzle_name):
	generations = range(len(avg_strategy))
	n = len(avg_strategy[0])
	m = n // 2
	fig, axes = plt.subplots(2, (n + 1) // 2) # round up

	fig.suptitle(f"Generation vs Strategy parameters ({puzzle_name})")

	avg_strategy = np.array(avg_strategy)
	max_strategy = np.array(max_strategy)
	min_strategy = np.array(min_strategy)

	skip = n % 2 != 0

	for i in range(m):
		axes[0, i].plot(generations, avg_strategy[:, i], label="Average strategy")
		axes[0, i].plot(generations, max_strategy[:, i], label="Max strategy")
		axes[0, i].plot(generations, min_strategy[:, i], label="Min strategy")
		axes[0, i].set_title(f"Strategy parameter {i+1}")
		axes[1, i].plot(generations, avg_strategy[:, m+skip+i], label="Average strategy")
		axes[1, i].plot(generations, max_strategy[:, m+skip+i], label="Max strategy")
		axes[1, i].plot(generations, min_strategy[:, m+skip+i], label="Min strategy")
		axes[1, i].set_title(f"Strategy parameter {m+skip+i+1}")

	if skip:
		axes[0, m].plot(generations, avg_strategy[:, m], label="Average strategy")
		axes[0, m].plot(generations, max_strategy[:, m], label="Max strategy")
		axes[0, m].plot(generations, min_strategy[:, m], label="Min strategy")
		axes[0, m].set_title(f"Strategy parameter {m+1}")

	# Hide x labels and tick labels for top plots and y ticks for right plots.
	for ax in axes.flat:
		ax.set(xlabel="Generation", ylabel="Strategy parameter")
		ax.label_outer()

	handles, labels = axes[0, 0].get_legend_handles_labels()
	fig.legend(handles, labels)

def plot_statistics(avg_fitness, max_fitness, min_fitness, avg_strategy, max_strategy, min_strategy, puzzle_name):
	plot_fitness(avg_fitness, max_fitness, min_fitness, puzzle_name)
	plot_strategy(avg_strategy, max_strategy, min_strategy, puzzle_name)
	plt.show()