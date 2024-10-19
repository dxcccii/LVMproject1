from z3 import *
import numpy as np
import time  # Import the time module

#########################################################################################################
# Recursive function that computes all possibilities of placing the remaining blocks,                   #
# starting at a given index                                                                             #
# 'constraints': list with blocks left to place;                                                        #
# 'i': placing index                                                                                    #
# 'sz': size of the row/column                                                                          #
# 'currPerm': current permutation of placing the blocks in the row/column                               #
# 'Perms': list with all possibilities of placing the blocks in the row/column according to constraints #
# 'Knowns': if not 'None', then permutations were previously computed and these some cells may already  #
#  have their value set (either to '1' or '0')
#########################################################################################################
def computePermsAux(constraints: list, i: int, sz: int, currPerm: list, Perms: list, Knowns: np.array=None):
    # Base case #1: index i is the end of the row/column; add the current permutation
    if i == sz:
        Perms.append(currPerm.copy())
        return

    # Base case #2: no blocks left to place; fill the row/column with zeros
    if len(constraints) == 0:
        if Knowns is not None and any(Knowns[i:] == 1):
            return
        currPerm[i:] = [0]*(sz - i)
        Perms.append(currPerm.copy())
        return
    
    # Possibility (i): place a blank space if possible
    whiteSpaces = sz - i - sum(constraints) - (len(constraints) - 1)
    if whiteSpaces > 0:
        if Knowns is None or not Knowns[i] == 1:
            currPerm[i] = 0
            computePermsAux(constraints, i+1, sz, currPerm, Perms)
    
    # Possibility (ii): place a block of the required size
    blockSize = constraints[0]
    if Knowns is not None and any(Knowns[i:i+blockSize] == 0):
        return
    currPerm[i:i+blockSize] = [1]*blockSize
    if len(constraints) > 1:
        if Knowns is not None and Knowns[i+blockSize] == 1:
            return
        currPerm[i+blockSize] = 0
        blockSize += 1
    computePermsAux(constraints[1:], i+blockSize, sz, currPerm, Perms)

#########################################################################################################
# Driver function to compute all possibilities (permutations) of fitting the blocks in in a row/column #
#########################################################################################################
def computePerms(constraints: list, sz: int, Knowns : np.array=None) -> list:
    Perms = []
    computePermsAux(constraints, 0, sz, [0]*sz, Perms, Knowns)
    return Perms

#############################################################################################
# Optimized function that checks if a Nonogram puzzle is well-posed                         #
#############################################################################################
def well_posed_optimized(V: list, H: list) -> (bool):
    s = Solver()
    R, C = len(H), len(V)

    # Measure the time for resolution
    start_time = time.time()  # Start timer

    P = [[Bool(f'p_{i}_{j}') for j in range(C)] for i in range(R)]

    # Precompute known literals from row and column constraints
    Paux = np.array([-1] * (R * C)).reshape((R, C))

    # Process rows
    for row, rowConstraint in enumerate(H):
        perms = np.array(computePerms(rowConstraint, C))
        permsSum = perms.sum(axis=0)
        Paux[row, permsSum == len(perms)] = 1  # Cell filled in all permutations
        Paux[row, permsSum == 0] = 0           # Cell blank in all permutations

    # Process columns
    for col, colConstraint in enumerate(V):
        perms = np.array(computePerms(colConstraint, R))
        permsSum = perms.sum(axis=0)
        Paux[permsSum == len(perms), col] = 1  # Cell filled in all permutations
        Paux[permsSum == 0, col] = 0           # Cell blank in all permutations

    # Add known values as constraints
    for r in range(R):
        for c in range(C):
            if Paux[r, c] == 1:
                s.add(P[r][c])
            elif Paux[r, c] == 0:
                s.add(Not(P[r][c]))

    # Horizontal Constraints
    for row, rowConstraint in enumerate(H):
        perms = computePerms(rowConstraint, C, Knowns=Paux[row,])
        s.add(Or( *(And([P[row][j] if p else Not(P[row][j]) for (j, p) in enumerate(pm)]) for pm in perms) ))

    # Vertical Constraints
    for col, colConstraint in enumerate(V):
        perms = computePerms(colConstraint, R, Knowns=Paux[:, col])
        s.add(Or( *(And([P[i][col] if p else Not(P[i][col]) for (i, p) in enumerate(pm)]) for pm in perms) ))


    # First SAT check (to find a solution)
    if s.check() == sat:
        m = s.model()

        # First solution
        sol1 = '\n'.join(['|' + '|'.join(['X' if is_true(m.evaluate(P[i][j])) else ' ' for j in range(C)]) + '|' for i in range(R)])

        # Add negation of the current solution (ensure at least one cell is different)
        s.add(Or( *(Not(P[i][j]) for i in range(R) for j in range(C) if is_true(m.evaluate(P[i][j]))) ))

        # Second SAT check (to look for another solution)
        if s.check() == sat:
            m = s.model()
            sol2 = '\n'.join(['|' + '|'.join(['X' if is_true(m.evaluate(P[i][j])) else ' ' for j in range(C)]) + '|' for i in range(R)])
            end_time = time.time()  # End timer
            elapsed_time = (end_time - start_time) * 1000  # Calculate time in milliseconds
            print(f"The problem is not well-posed: it has more than one solution:\n{sol1}\nand\n{sol2}")
            print(f"Resolution time: {elapsed_time:.2f} milliseconds")
            return False
        end_time = time.time()  # End timer
        elapsed_time = (end_time - start_time) * 1000  # Calculate time in milliseconds
        print(f"The problem is well-posed! Solution:\n{sol1}")
        print(f"Resolution time: {elapsed_time:.2f} milliseconds")
        return True
    else:
        end_time = time.time()  # End timer
        elapsed_time = (end_time - start_time) * 1000  # Calculate time in milliseconds
        print('The problem is not well-posed: it has no solution!')
        print(f"Resolution time: {elapsed_time:.2f} milliseconds")
        return False

#############################################################################################
# Function that verifies if the constraints are valid: all block sizes are positive and fit #
#############################################################################################
def checkConstraints(H : list, V : list) -> bool:
    R, C = len(H), len(V)
    for h_const in H:
        if not all([c > 0 for c in h_const]):
            print(f"Invalid Horizontal Constraint {h_const}: All values must be positive\nExiting...")
            return False
        if sum(h_const) + len(h_const) - 1 > C:
            print(f"Invalid Horizontal Constraint {h_const}: Needed length ({sum(h_const) + len(h_const) - 1}) exceeds number of columns ({C})\nExiting...")
            return False
    for v_const in V:
        if not all([c > 0 for c in v_const]):
            print(f"Invalid Vertical Constraint {v_const}: All values must be positive\nExiting...")
            return False
        if sum(v_const) + len(v_const) - 1 > R:
            print(f"Invalid Vertical Constraint {v_const}: Needed length ({sum(v_const) + len(v_const) - 1}) exceeds number of rows ({R})\nExiting...")
            return False
    return True

#############################################################################################
# Example usage
#############################################################################################
if __name__ == "__main__":
    ## Well-posed Nonogram (5x5 grid)
    #V_well = [[1], [1], [1], [1], [1]]
    #H_well = [[1], [1], [1], [1], [1]]

    ## Not well-posed Nonogram (5x5 grid)
    #V_not_well = [[1], [1], [1], [1], [1]]
    #H_not_well = [[1], [2], [1], [1], [1]]

    # 25x25 puzzle, not well-posed, NO SOLUTION?
    #H = [[6, 1], [5, 2], [18], [6, 1], [11], [7, 1], [6], [4, 1], [1, 7], [7, 5], [4, 10], [5, 10], [8, 4, 2], [13], [4, 1], [9, 1, 4], [12, 7], [13], [8], [11, 7], [2, 3, 4], [10], [19], [3, 3], [4, 5]]
    #V = [[1, 3, 1], [1, 4], [1, 4, 4], [1, 4, 1], [1, 4, 1], [1, 5, 1], [1, 4, 1], [3, 1, 1], [3, 1, 5], [3, 1, 1], [2, 1, 1], [4, 1], [4, 6], [1, 2, 6], [4, 1], [4, 1], [4, 1, 1], [4, 1, 2], [4, 1, 2], [6, 1, 3], [4, 1, 1], [1, 1, 1], [1, 2, 1], [1, 2, 1], [1, 3, 1]]

    # 25x25 puzzle, well-posed
    #H = [[6,10,3],[4,6,7],[18],[6,10,3],[11,1,1],[7,8],[6,1,1],[4,8],[1,3,7],[7,5,2,1],[4,10,2],[5,10,2],[8,6,4,2],[13,3],[4,8],[9,2,1,4],[12,7,1],[13,3,2],[8,4],[11,7,1],[2,3,4,3],[10,11],[19],[3,3,9],[4,5,7,1]]
    #V = [[1,3,1,3,8,1],[1,4,15],[1,4,10,4],[1,4,16],[1,4,1,12],[1,5,1,2,10],[1,4,1,2,5,4],[3,1,1,1,2,5,4],[3,1,5,1,3,1,2,1],[3,1,1,6,2,1,2,1],[2,1,1,4,3,1,1],[4,1,5,3,1],[4,6,1,1],[1,2,6,1,1,1],[4,1,5,1,2,1],[4,1,4,2,1,2,1],[4,1,1,2,1,2,6],[4,1,2,2,2,2,6],[4,1,2,3,2,6],[6,1,3,1,3,2],[4,1,1,1,1,1,1,1,1],[1,1,1,1,1,3,1,1,1],[1,2,1,3,1,2,1],[1,2,1,3,1,2,2,1],[1,3,1,4,7,2]]

    # 25x25 puzzle, not well-posed (multiple solutions expected)
    H = [[5], [5], [5], [5], [5], 
     [3, 1], [3, 1], [3, 1], [3, 1], [3, 1], 
     [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
     [5], [5], [5], [5], [5], 
     [2, 2], [2, 2], [2, 2], [2, 2], [2, 2]]

    V = [[5], [5], [5], [5], [5], 
     [3, 1], [3, 1], [3, 1], [3, 1], [3, 1], 
     [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
     [5], [5], [5], [5], [5], 
     [2, 2], [2, 2], [2, 2], [2, 2], [2, 2]]

    print("Checking well-posedness of Nonogram:")
    if not checkConstraints(H, V):
        exit(1)
    well_posed_optimized(V, H)

