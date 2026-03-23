def load_puzzle(name):
	
	file = open("puzzles/" + name + ".txt", "r")

	puzzle = {
		"data": [],
		"walls": 0,
		"optimal": 0
	}

	for line in file:

		line = line.strip()

		if ":" in line:
			props = line.split(":")
			key = props[0].strip()
			val = props[1].strip()

			if key in puzzle and key != "data":
				puzzle[key] = int(val)

		elif len(line) > 0:
			puzzle["data"].append(line)
		
	return puzzle