from abc import ABC, abstractmethod

class PuzzleSolver(ABC):
    def __init__(self, puzzle):
        self.puzzle = puzzle

    @abstractmethod
    def print_setup(self):
        pass

    @abstractmethod
    def initialize_population(self):
        pass

    @abstractmethod
    def run_generation(self):
        pass

    @abstractmethod
    def fitness(self, solution):
        pass

    @abstractmethod
    def mutate(self, solution):
        pass

    @abstractmethod
    def crossover(self, *solutions):
        pass

    @abstractmethod
    def pprint_solution(self, solution):
        pass

    @abstractmethod
    def best_solution(self):
        pass