# enclose.horse solver

## Organization

- `horse.py`: contains the runner and the main EA for solving enclose.horse puzzles
- `plot_stats.py`: contains auxiliary functions for constructing plots via matplotlib
- `puzzle_loader.py`: contains a helper function to load puzzle data encoded in a predefined text format
- `puzzles/*.txt`: puzzle data encoded encoded in a predefined text format

## Puzzle storage format

Puzzles are stored as plaintext files adhering to the following schema:

```
walls: <NUM_WALLS>
optimal: <OPTIMAL_ENCLOSED_AREA>

<GRID_STATE>
```

`<NUM_WALLS>`: (int) the number of walls in a solution\
`<OPTIMAL_ENCLOSED_AREA>`: (int) the enclosed area for an optimal solution \
`<GRID_STATE>`: (string) a string with n lines where each line contains m characters where the mth character on the nth line stores the tile type at position (m, n) on the puzzle grid.

## How the program works

The main program `horse.py` performs the following steps:
1. Load the puzzle selected via `PUZZLE_NAME` by reading the corresponding text file under the `puzzles/` directory.
2. Find all valid wall positions and the horse position as well as perform preprocessing steps.
3. Initialize population and set parameters.
4. Open a file handle to a CSV file `last_run.csv` store data to be collected during the run.
5. Run the EA for `MAX_GENERATIONS` number of generations, while collecting and printing data and statistics for each generation.
6. Print best solution found by the EA.
7. Flush written data to `last_run.csv`
8. (Optional) Show plots of statistics.

## How to run the program

The main program `horse.py` can be run by executing the following command

```sh
python3 horse.py
```

### Changing puzzles

The puzzle loaded by the program can be changed via the constant `PUZZLE_NAME` in `horse.py`. For instance, to change the puzzle to run the EA on to be `bees`. Makethe following change to line 14 in `horse.py`.

```diff

# Define puzzles in the /puzzles folder
- PUZZLE_NAME = "day46"
+ PUZZLE_NAME = "bees"

```

### Showing plots

The constant `SHOW_PLOTS` controls whether a plot of statistics is shown at the end of a run. By default, it's value is set to `TRUE` which displays the configured plots in `plot_stats.py` using matplotlib.

> [!NOTE]
> The python packages `matplotlib` and `numpy` are required to view the plots. They can be installed the following command:
>
> ```sh
> pip install matplotlib numpy
> ```

There are two plots available to be viewed - one for the strategy parameter (mutation step size) and one for fitness. Both plots graphs the average, maximum and minimum of their respective statistics versus the generation number.