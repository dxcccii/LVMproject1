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
def computePermsAux(constraints: list, i: int, sz: int, currPerm: list, Perms: list):
    # Base case #1: index i is the end of the row/column; add the current permutation
    #  to the list of possibilities and return
    if i == sz:
        Perms.append(currPerm.copy())
        return
    
    # Base case #2: no blocks left to place; fill the row/column with zeros (blank spaces),
    #  add the current permutation to the list of possibilities and return
    if len(constraints) == 0:
        currPerm[i:] = [0]*(sz - i)
        Perms.append(currPerm.copy())
        return
    
    # There are two possibilities: 
    #   (i) put a blank space (if possible) at the current index, i; or
    #   (ii) place the next block starting at index i and, if needed, a blank space after the block. 

    # Possibility (i)
    # compute the number of blank spaces that can still be placed, given by the number of cells left to fill subtracted by the
    # sum of block left to place and minimum number of blank spaces that must be placed between them.
    whiteSpaces = sz - i - sum(constraints) - (len(constraints) - 1)
    # check if a blank space can be placed; if so, do it and place the remaining blocks starting at index i+1
    if whiteSpaces > 0:
        currPerm[i] = 0
        computePermsAux(constraints, i+1, sz, currPerm, Perms)

    # Possibility (ii)
    # size of the next block to be placed
    blockSize = constraints[0]
    # place the block
    currPerm[i:i+blockSize] = [1]*blockSize
    # if there are still blocks needing placing, add a blank space after the block just placed
    if len(constraints) > 1:
        currPerm[i+blockSize] = 0
        blockSize += 1
    # place the remaining blocks after this one
    computePermsAux(constraints[1:], i+blockSize, sz, currPerm, Perms)

########################################################################################################
# Driver function to compute all possibilities (permutations) of fitting the blocks in in a row/column #
# 'constraints': block to place in the row/column                                                      #
# 'sz': length of the row/column                                                                       #
# Returns: list with all permutations                                                                  #
########################################################################################################
def computePerms(constraints: list, sz: int) -> list:
    Perms = []
    computePermsAux(constraints, 0, sz, [0]*sz, Perms)
    return Perms

#############################################################################################
# Function that solves a Nonogram puzzle, encoded as a SAT problem, using the Z3 SAT solver #
# 'V': vertical constraints                                                                 #
# 'H': horizontal constraints                                                               #
# Returns: (sat, solvedPuzzle), if satisfiable; (unsat, []), otherwise, where solvedPuzzle  #
#  is a string with the solution of the puzzle in a human-readable format                   #
#############################################################################################
def nonogram(V: list, H: list) -> (bool, list): 
    # Number of rows and columns, respectively
    R, C = len(H), len(V)
    s = Solver()

    start_time = time.time()  # Start timer

    # Boolean variables: 
    #  p_i_j is 1 if the cell at row i column j is filled black, and 0 if the cell is blank (0-indexed)
    P = [[Bool(f'p_{i}_{j}') for j in range(C)] for i in range(R)]

    # Horizontal Constraints
    for row, rowConstraint in enumerate(H):
        # Compute all possibilities of fitting the blocks, according to constraint 'rowConstraint', 
        #  in row 'row'
        perms = computePerms(rowConstraint, C)
        # For a given permutation, variables p_row_j are And'ed, for 0 <= j < C;
        #  if entry j of the permutation is '1', the literal is p_row_j, and if '0' the literal is negated (Not(p_row_j))
        # All permutations for the row are Or'ed together
        s.add(Or( *(And([P[row][j] if p else Not(P[row][j]) for (j, p) in enumerate(pm)]) for pm in perms) ))

    # Vertical Constraints
    for col, colConstraint in enumerate(V):
        # Compute all possibilities of fitting the blocks, according to constraint 'colConstraint', 
        #  in col 'col'
        perms = computePerms(colConstraint, R)
        # Cognate to the row constraints
        s.add(Or( *(And([P[i][col] if p else Not(P[i][col]) for (i, p) in enumerate(pm)]) for pm in perms) ))

    if s.check() == sat:
        # If the puzzle is solvable (SAT problem is satisfiable), print the solution in a human-readable format
        m = s.model()
        solvedPuzzle = '\n'.join(['|' + '|'.join(['X' if m[P[i][j]] else ' ' for j in range(C)]) + '|' for i in range(R)])
        end_time = time.time()  # End timer
        elapsed_time = (end_time - start_time) * 1000  # Calculate time in milliseconds
        print(f'Found a solution:\n{solvedPuzzle}')
        print(f"Resolution time: {elapsed_time:.2f} milliseconds")
        return (sat, solvedPuzzle)

    else:
        # Otherwise, return unsat
        end_time = time.time()  # End timer
        elapsed_time = (end_time - start_time) * 1000  # Calculate time in milliseconds
        print('No solution found')
        print(f"Resolution time: {elapsed_time:.2f} milliseconds")
        return (unsat, [])

#############################################################################################
# Function that checks if a Nonogram puzzle is well-posed, that is, if it has a unique      #
#  solution. Encodes the puzzle as a SAT problem, as in function 'nonogram()'. If the       #
#  puzzle is not well-posed because there are multiple solutions, the function prints two   #
#  solutions. If the puzzle is not well-posed because there is not solution, it states so.  #
# 'V': vertical constraints                                                                 #
# 'H': horizontal constraints                                                               #
# Returns: True, if the puzzle is well-posed; and False, otherwise.                         #
#############################################################################################
def well_posed(V: list, H: list) -> (bool):
    s = Solver()
    R, C = len(H), len(V)

    start_time = time.time()  # Start timer

    P = [[Bool(f'p_{i}_{j}') for j in range(C)] for i in range(R)]

    for row, rowConstraint in enumerate(H):
        perms = computePerms(rowConstraint, C)
        s.add(Or( *(And([P[row][j] if p else Not(P[row][j]) for (j, p) in enumerate(pm)]) for pm in perms) ))

    for col, colConstraint in enumerate(V):
        perms = computePerms(colConstraint, R)
        s.add(Or( *(And([P[i][col] if p else Not(P[i][col]) for (i, p) in enumerate(pm)]) for pm in perms) ))

    # Solves the SAT problem just as function 'nonogram()'. However, it checks for multiple solutions 
    if s.check() == sat:
        m = s.model()
        # Negates the current solution by And'ing all positive literals and negating the And (equivalently, 
        #  Or's the negation of all positive literals in the computed solution)
        s.add(Or( *(Not(P[i][j]) for j in range(C) for i in range(R) if m[P[i][j]]) ))
        # Saves the first computed solution for printing, if needed
        sol1 = '\n'.join(['|' + '|'.join(['X' if m[P[i][j]] else ' ' for j in range(C)]) + '|' for i in range(R)])
        # Checks for a second solution
        if s.check() == sat:
            m = s.model()
            sol2 = '\n'.join(['|' + '|'.join(['X' if m[P[i][j]] else ' ' for j in range(C)]) + '|' for i in range(R)])
            end_time = time.time()  # End timer
            elapsed_time = (end_time - start_time) * 1000  # Calculate time in milliseconds
            print(f"The problem is not well-posed: it has more than one solution:\n{sol1}\nand\n{sol2}")
            print(f"Resolution time: {elapsed_time:.2f} milliseconds")
            return False
        end_time = time.time()  # End timer
        elapsed_time = (end_time - start_time) * 1000  # Calculate time in milliseconds
        print("The problem is well-posed!")
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
#  within the row/colum.                                                                    #
# 'V': vertical constraints                                                                 #
# 'H': horizontal constraints                                                               #
# Returns: True, if the constraints are valid; and False, otherwise.                        #
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

if __name__ == "__main__":
    ## Project assignement puzzle, 10x5, well-posed
    # V = [[2,1],[2,1,3],[7],[1,3],[2,1]]
    # H = [[2],[2,1],[1,1],[3],[1,1],[1,1],[2],[1,1],[1,2],[2]]

    ## Simple, not well-posed puzzle (5x5)
    # V = [[1],[1],[1],[1],[1]]
    # H = [[1],[1],[1],[1],[1]]

    ## 10x10 puzzle, well-posed
    # V = [[1,2],[1,3],[1,8],[2,7],[6],[4],[4,1,2],[2,3],[1,4],[1,4]]
    # H = [[4],[2,2],[3,6],[7],[6],[4],[3,1,2],[2,3],[2,4],[2,4]]

    ## 15x15 puzzle, well-posed
    # V = [[1,3,1],[6,5],[7,1,1,1],[8,1,1,1],[7,1,1,1],[6,5],[1,3,1,2],[1,2],[1,3,2],[11],[1,7,4],[15],[2,7,4],[2,11],[2,1,3,1]]
    # H = [[1,4],[3,5],[5,1],[7,3],[5,5],[5,7],[5,5],[7,5],[1,1,5],[7,7],[1,1,2,1,2],[14],[1,1,5],[14],[9]]

    ## 25x25 puzzle, well-posed
    H = [[6,10,3],[4,6,7],[18],[6,10,3],[11,1,1],[7,8],[6,1,1],[4,8],[1,3,7],[7,5,2,1],[4,10,2],[5,10,2],[8,6,4,2],[13,3],[4,8],[9,2,1,4],[12,7,1],[13,3,2],[8,4],[11,7,1],[2,3,4,3],[10,11],[19],[3,3,9],[4,5,7,1]]
    V = [[1,3,1,3,8,1],[1,4,15],[1,4,10,4],[1,4,16],[1,4,1,12],[1,5,1,2,10],[1,4,1,2,5,4],[3,1,1,1,2,5,4],[3,1,5,1,3,1,2,1],[3,1,1,6,2,1,2,1],[2,1,1,4,3,1,1],[4,1,5,3,1],[4,6,1,1],[1,2,6,1,1,1],[4,1,5,1,2,1],[4,1,4,2,1,2,1],[4,1,1,2,1,2,6],[4,1,2,2,2,2,6],[4,1,2,3,2,6],[6,1,3,1,3,2],[4,1,1,1,1,1,1,1,1],[1,1,1,1,1,3,1,1,1],[1,2,1,3,1,2,1],[1,2,1,3,1,2,2,1],[1,3,1,4,7,2]]
    
    # 25x25 puzzle, not well-posed (multiple solutions expected)
    # H = [[5], [5], [5], [5], [5], 
    #  [3, 1], [3, 1], [3, 1], [3, 1], [3, 1], 
    #  [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
    #  [5], [5], [5], [5], [5], 
    #  [2, 2], [2, 2], [2, 2], [2, 2], [2, 2]]
    # V = [[5], [5], [5], [5], [5], 
    #  [3, 1], [3, 1], [3, 1], [3, 1], [3, 1], 
    #  [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
    #  [5], [5], [5], [5], [5], 
    #  [2, 2], [2, 2], [2, 2], [2, 2], [2, 2]]

    if not checkConstraints(H, V):
        exit(1)

    print("Solving Nonogram:")
    nonogram(V, H)
    
    print("\nChecking well-posedness:")
    well_posed(V, H)
