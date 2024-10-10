from z3 import Solver, Bool, And, Or, Not, sat

# helper function: applies constraints to the rows or columns of the nonogram
# `cells`: a list of Z3 Boolean variables representing the cells of a row or column
# `constraints`: a list of integers representing the required block lengths in this row or column
def apply_constraints(cells, constraints):
    # if there are no constraints all cells are unfilled
    if not constraints:
        return And([Not(c) for c in cells])  # All cells should be "false" (unfilled)

    n = len(cells)  # number of cells in the row or column

    # recursive function that attempts to place blocks starting from the given index
    # `start`: index where we begin placing the next block
    # `remaining_constraints`: list of remaining block lengths that need to be placed
    def place_blocks(start, remaining_constraints):
        # base case: if no more constraints (no more blocks to place), ensure all remaining cells are unfilled
        if not remaining_constraints:
            return And([Not(cells[i]) for i in range(start, n)])  # Unfilled cells for the rest of the row/column

        # get the size of the next block to place
        block_size = remaining_constraints[0]
        # get the list of remaining blocks after this one
        rest = remaining_constraints[1:]

        # list to store all possible valid placements for the current block
        block_formulas = []

        # tries to place the current block at each valid starting position
        # a block of size `block_size` can start anywhere from `start` to `n - block_size`
        for i in range(start, n - block_size + 1):
            # ensure the next `block_size` cells are filled (true)
            block = And([cells[j] for j in range(i, i + block_size)])

            # if there are more blocks after this, we need a gap after this one
            if rest and i + block_size < n:
                block = And(block, Not(cells[i + block_size]))  # Add a gap after the block

            # recursively places the remaining blocks after this one
            block_formulas.append(And(block, place_blocks(i + block_size + 1, rest)))

        # return the formula that allows placing the block at any valid starting position
        return Or(block_formulas)
    
    # start placing blocks from the beginning of the row/column (index 0)
    return place_blocks(0, constraints)

# nonogram solver function
# `V`: vertical constraints
# `H`: horizontal constraints
def nonogram(V, H):
    num_cols = len(V)  # number of columns in the grid
    num_rows = len(H)  # number of rows in the grid
    
    # create Z3 Boolean variables for each cell in the grid
    # each cell where r is the row and c is the column
    grid = [[Bool(f'cell_{r}_{c}') for c in range(num_cols)] for r in range(num_rows)]
    
    # create a Z3 solver object
    s = Solver()

    # add the constraints for each row 
    for r in range(num_rows):
        # apply the corresponding row constraints and add them to the solver
        s.add(apply_constraints(grid[r], H[r]))

    # add the constraints for each column 
    for c in range(num_cols):
        # collect the cells in the current column
        column_cells = [grid[r][c] for r in range(num_rows)]
        # apply the corresponding column constraints and add them to the solver
        s.add(apply_constraints(column_cells, V[c]))

    # check if a solution exists
    if s.check() == sat:
        # if satisfiable, extract the solution (model) from the solver
        model = s.model()
        # return the solution grid as a list of lists (1 for filled, 0 for unfilled)
        return [[1 if model[grid[r][c]] == True else 0 for c in range(num_cols)] for r in range(num_rows)]
    else:
        # if no solution exists, return None
        return None

# function to check if the nonogram is well-posed
# `V`: vertical constraints
# `H`: horizontal constraints
def well_posed(V, H):
    # first, solve the nonogram to get an initial solution
    solution = nonogram(V, H)
    
    if not solution:
        return False  # if no solution exists, the puzzle is not well-posed
    
    num_rows = len(H)  # number of rows
    num_cols = len(V)  # number of columns
    
    # re-create the Z3 Boolean variables for each cell in the grid
    grid = [[Bool(f'cell_{r}_{c}') for c in range(num_cols)] for r in range(num_rows)]
    
    # create a new Z3 solver object
    s = Solver()

    # re-add the row constraints to the new solver
    for r in range(num_rows):
        s.add(apply_constraints(grid[r], H[r]))
    
    # re-add the column constraints to the new solver
    for c in range(num_cols):
        column_cells = [grid[r][c] for r in range(num_rows)]
        s.add(apply_constraints(column_cells, V[c]))
    
    # exclude the first solution so that if the solver finds another solution, it must be different from the first one
    exclusion_constraint = Or([grid[r][c] != (solution[r][c] == 1) for r in range(num_rows) for c in range(num_cols)])
    s.add(exclusion_constraint)

    # check if another solution exists
    if s.check() == sat:
        return False  # another solution exists, so the puzzle is not well-posed 
    else:
        return True  # no other solution exists, so the puzzle is well-posed

# constraints for the nonogram
V = [[3], [2, 1], [2, 2], [3, 1], [1, 1], [2], [4], [1, 3], [1, 1], [4]]  # vertical constraints (columns)
H = [[1], [4], [1, 3], [5], [2], [3, 1], [1, 3], [2, 1], [3], [3]]        # horizontal constraints (rows)

# solve the nonogram and display the solution
solution = nonogram(V, H)
if solution:
    print("Nonogram Solution:")
    for row in solution:
        print(row)  # print each row of the solution as a list of 1s (filled) and 0s (unfilled)
else:
    print("No solution found")

# check if the nonogram has a unique solution (is well-pose or not)
if well_posed(V, H):
    print("The puzzle is well-posed (has a unique solution).")
else:
    print("The puzzle is not well-posed (does not have a unique solution).")
