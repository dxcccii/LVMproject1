from z3 import Solver, Bool, And, Or, Not, sat

# Helper function: applies constraints to the rows or columns of the nonogram
# `cells`: a list of Z3 Boolean variables representing the cells of a row or column
# `constraints`: a list of integers representing the required block lengths in this row or column
def apply_constraints(cells, constraints):
    # If there are no constraints (empty row/column), all cells must be unfilled (false)
    if not constraints:
        return And([Not(c) for c in cells])  # All cells should be "false" (unfilled)

    n = len(cells)  # Number of cells in the row or column

    # Recursive helper function that attempts to place blocks starting from a given index
    # `start`: index where we begin placing the next block
    # `remaining_constraints`: list of remaining block lengths that need to be placed
    def place_blocks(start, remaining_constraints):
        # Base case: if no more constraints (no more blocks to place), ensure all remaining cells are unfilled
        if not remaining_constraints:
            return And([Not(cells[i]) for i in range(start, n)])  # Unfilled cells for the rest of the row/column

        # Get the size of the next block to place
        block_size = remaining_constraints[0]
        # Get the list of remaining blocks after this one
        rest = remaining_constraints[1:]

        # List to store all possible valid placements for the current block
        block_formulas = []

        # Try placing the current block at each valid starting position
        # A block of size `block_size` can start anywhere from `start` to `n - block_size`
        for i in range(start, n - block_size + 1):
            # Ensure the next `block_size` cells are filled (true)
            block = And([cells[j] for j in range(i, i + block_size)])

            # If there are more blocks after this one, we need a gap (an unfilled cell) after the current block
            if rest and i + block_size < n:
                block = And(block, Not(cells[i + block_size]))  # Add a gap after the block

            # Recursively place the remaining blocks after this one
            block_formulas.append(And(block, place_blocks(i + block_size + 1, rest)))

        # Return the formula that allows placing the block at any valid starting position
        return Or(block_formulas)
    
    # Start placing blocks from the beginning of the row/column (index 0)
    return place_blocks(0, constraints)

# Nonogram solver function
# `V`: vertical constraints (one list for each column)
# `H`: horizontal constraints (one list for each row)
def nonogram(V, H):
    num_cols = len(V)  # Number of columns in the grid
    num_rows = len(H)  # Number of rows in the grid
    
    # Create Z3 Boolean variables for each cell in the grid
    # Each cell is represented by a unique variable named 'cell_r_c' where r is the row and c is the column
    grid = [[Bool(f'cell_{r}_{c}') for c in range(num_cols)] for r in range(num_rows)]
    
    # Create a Z3 solver object
    s = Solver()

    # Add constraints for each row (horizontal constraints)
    for r in range(num_rows):
        # Apply the corresponding row constraints and add them to the solver
        s.add(apply_constraints(grid[r], H[r]))

    # Add constraints for each column (vertical constraints)
    for c in range(num_cols):
        # Collect the cells in the current column
        column_cells = [grid[r][c] for r in range(num_rows)]
        # Apply the corresponding column constraints and add them to the solver
        s.add(apply_constraints(column_cells, V[c]))

    # Check if the constraints are satisfiable (i.e., if a solution exists)
    if s.check() == sat:
        # If satisfiable, extract the model (solution) from the solver
        model = s.model()
        # Return the solution grid as a list of lists (1 for filled, 0 for unfilled)
        return [[1 if model[grid[r][c]] == True else 0 for c in range(num_cols)] for r in range(num_rows)]
    else:
        # If no solution exists, return None
        return None

# Function to check if the nonogram is well-posed (i.e., it has a unique solution)
# `V`: vertical constraints
# `H`: horizontal constraints
def well_posed(V, H):
    # First, solve the nonogram to get an initial solution
    solution = nonogram(V, H)
    
    if not solution:
        return False  # If no solution exists, the puzzle is not well-posed
    
    num_rows = len(H)  # Number of rows
    num_cols = len(V)  # Number of columns
    
    # Re-create the Z3 Boolean variables for each cell in the grid
    grid = [[Bool(f'cell_{r}_{c}') for c in range(num_cols)] for r in range(num_rows)]
    
    # Create a new Z3 solver object
    s = Solver()

    # Re-add the row constraints to the new solver
    for r in range(num_rows):
        s.add(apply_constraints(grid[r], H[r]))
    
    # Re-add the column constraints to the new solver
    for c in range(num_cols):
        column_cells = [grid[r][c] for r in range(num_rows)]
        s.add(apply_constraints(column_cells, V[c]))
    
    # Add a constraint to exclude the current solution
    # This ensures that if the solver finds another solution, it must be different from the first one
    exclusion_constraint = Or([grid[r][c] != (solution[r][c] == 1) for r in range(num_rows) for c in range(num_cols)])
    s.add(exclusion_constraint)

    # Check if another solution exists
    if s.check() == sat:
        return False  # Another solution exists, so the puzzle is not well-posed (not unique)
    else:
        return True  # No other solution exists, so the puzzle is well-posed (unique solution)

# Example constraints for the nonogram
V = [[3], [2, 1], [2, 2], [3, 1], [1, 1], [2], [4], [1, 3], [1, 1], [4]]  # Vertical constraints (columns)
H = [[1], [4], [1, 3], [5], [2], [3, 1], [1, 3], [2, 1], [3], [3]]        # Horizontal constraints (rows)

# Solve the nonogram and display the solution
solution = nonogram(V, H)
if solution:
    print("Nonogram Solution:")
    for row in solution:
        print(row)  # Print each row of the solution as a list of 1s (filled) and 0s (unfilled)
else:
    print("No solution found")

# Check if the puzzle is well-posed (i.e., it has a unique solution)
if well_posed(V, H):
    print("The puzzle is well-posed (has a unique solution).")
else:
    print("The puzzle is not well-posed (does not have a unique solution).")
