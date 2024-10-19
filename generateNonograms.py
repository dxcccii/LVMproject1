import sys
import random

def generate_valid_nonogram(L, C):
    # Create a random valid 10x10 grid of 0 (empty) and 1 (filled) without empty rows/columns
    while True:
        grid = [[random.randint(0, 1) for _ in range(C)] for _ in range(L)]
        
        # Check if all rows and columns contain at least one '1'
        if all(any(cell == 1 for cell in row) for row in grid) and \
           all(any(grid[row_idx][col_idx] == 1 for row_idx in range(L)) for col_idx in range(C)):
            break
    
    # Generate clues for rows
    row_clues = []
    for row in grid:
        row_clue = []
        count = 0
        for cell in row:
            if cell == 1:
                count += 1
            else:
                if count > 0:
                    row_clue.append(count)
                count = 0
        if count > 0:
            row_clue.append(count)
        row_clues.append(row_clue if row_clue else [0])
    
    # Generate clues for columns
    col_clues = []
    for col_idx in range(C):
        col_clue = []
        count = 0
        for row_idx in range(L):
            if grid[row_idx][col_idx] == 1:
                count += 1
            else:
                if count > 0:
                    col_clue.append(count)
                count = 0
        if count > 0:
            col_clue.append(count)
        col_clues.append(col_clue if col_clue else [0])
    
    return grid, row_clues, col_clues


def generateNonograms(L, C=0, N=5):
    if C == 0:
        C = L
    # Generate 5 valid 10x10 Nonogram puzzles
    valid_nonograms_grid = []
    valid_nonograms_constraints = []
    for _ in range(N):
        grid, row_clues, col_clues = generate_valid_nonogram(L,C)
        valid_nonograms_grid.append(grid)
        valid_nonograms_constraints.append((row_clues, col_clues))
        # print(f"H = {row_clues}\nV = {col_clues}\n")
    return valid_nonograms_constraints


if __name__ == "__main__":
    generateNonograms(int(sys.argv[1]))


