from z3 import *
import numpy as np
import os

from time import perf_counter_ns as time

from generateNonograms import generateNonograms

PermsTime = 0
SolveTime = 0
SetupTime = 0
AddTimes = 0
TotalPerms = 0
WellPosedTime = 0

def readPuzzle(name: str) -> tuple:
    with open(f"RealPuzzles/{name}.txt") as f_in:
        lines = f_in.read().splitlines()  
        R, C = map(int,lines[0].strip().split())
        H = list( [list(map(int, l.strip().split())) for l in lines[1:R+1]])      
        V = list( [list(map(int, l.strip().split())) for l in lines[R+1:] ])  
        return (H, V)


def computePermsAux(constraints: list, i: int, sz: int, currPerm: list, Perms: list, Knowns: np.array=None):
    if i == sz:
        Perms.append(currPerm.copy())
        return

    if len(constraints) == 0:
        if Knowns is not None and any(Knowns[i:] == 1):
            return
        currPerm[i:]= [0]*(sz - i)
        Perms.append(currPerm.copy())
        return
    
    whiteSpaces = sz - i - sum(constraints) - (len(constraints) - 1)
    
    if whiteSpaces > 0:
        if Knowns is None or not Knowns[i] == 1:
            currPerm[i] = 0
            computePermsAux(constraints, i+1, sz, currPerm, Perms, Knowns)
    
    nOnes = constraints[0]
    if Knowns is not None and any(Knowns[i:i+nOnes] == 0):
        return
    currPerm[i:i+nOnes] = [1]*nOnes
    if len(constraints) > 1:
        if Knowns is not None and Knowns[i+nOnes] == 1:
            return
        currPerm[i+nOnes] = 0
        nOnes += 1
    computePermsAux(constraints[1:], i+nOnes, sz, currPerm, Perms, Knowns)



def computePerms(constraints: list, sz: int, Knowns : np.array=None) -> list:
    if not all([c > 0 for c in constraints]):
        print(f"Invalid Constraint {constraints}: All values must be positive\nExiting...")
        exit(1)
    if sum(constraints) + len(constraints) - 1 > sz:
        print(f"Invalid Constraint {constraints}: Needed length ({sum(constraints) + len(constraints) - 1}) exceeds max length ({sz})\nExiting...")
        exit(2)
    Perms = []
    computePermsAux(constraints, 0, sz, [0]*sz, Perms, Knowns)
    return Perms



def nonogram(V: list, H: list) -> (bool,list):
    global SetupTime, PermsTime, SolveTime, AddTimes, TotalPerms
    R, C = len(H), len(V)
    SetupTime = -time()
    s = Solver()

    P = [[Bool(f'p_{i}_{j}') for j in range(C)] for i in range(R)]

    # Horizontal Constraints:
    for row, rowConstraint in enumerate(H):
        PermsTime -= time()
        perms = computePerms(rowConstraint, C)
        PermsTime += time()
        TotalPerms += len(perms)
        AddTimes -= time()
        s.add(Or( *(And( [P[row][j] if p else Not(P[row][j]) for (j,p) in enumerate(pm)]) for pm in perms) ))
        AddTimes += time()

    # Vertical Constraints:
    for col, colConstraint in enumerate(V):
        PermsTime -= time()
        perms = computePerms(colConstraint, R)
        PermsTime += time()
        TotalPerms += len(perms)
        AddTimes -= time()
        s.add(Or( *(And( [P[i][col] if p else Not(P[i][col]) for (i,p) in enumerate(pm)]) for pm in perms) ))
        AddTimes += time()

    SetupTime += time()

    print(f"{TotalPerms}", end=" ")

    SolveTime = -time()

    if s.check() == sat:
        SolveTime += time()
        m = s.model()
        solvedPuzzle = '\n'.join(['|' + '|'.join(['X' if m[P[i][j]] else ' ' for j in range(C)]) + '|' for i in range(R)])
        # print(f'Found a solution:\n{solvedPuzzle}')
        return (sat, solvedPuzzle)

    else:
        SolveTime += time()
        # print('No solution found')
        return (unsat,[])



def well_posed(V: list, H: list) -> (bool):
    global SetupTime, PermsTime, SolveTime, AddTimes, TotalPerms, WellPosedTime
    SetupTime = -time()
    s = Solver()
    R, C = len(H), len(V)

    P = [[Bool(f'p_{i}_{j}') for j in range(C)] for i in range(R)]

    PermsTime -= time()
    Paux = np.array([-1] * (R*C)).reshape((R, C))
    for row, rowConstraint in enumerate(H):
        perms = np.array(computePerms(rowConstraint, C))
        permsSum = perms.sum(axis=0)
        Paux[row, permsSum == len(perms)] = 1
        Paux[row, permsSum == 0] = 0
    for col, colConstraint in enumerate(V):
        perms = np.array(computePerms(colConstraint, R))
        permsSum = perms.sum(axis=0)
        Paux[permsSum == len(perms), col] = 1
        Paux[permsSum == 0, col] = 0

    for r in range(R):
        for c in range(C):
            if Paux[r,c] == 1:
                s.add(P[r][c])
            if Paux[r,c] == 0:
                s.add(Not(P[r][c]))     
    PermsTime += time()       

    # Horizontal Constraints:
    for row, rowConstraint in enumerate(H):
        PermsTime -= time()
        perms = computePerms(rowConstraint, C, Knowns=Paux[row,])
        PermsTime += time()
        TotalPerms += len(perms)
        AddTimes -= time()
        s.add(Or( *(And( [P[row][j] if p else Not(P[row][j]) for (j,p) in enumerate(pm) if Paux[row,j] == -1]) for pm in perms) ))
        AddTimes += time()

    # Vertical Constraints:
    for col, colConstraint in enumerate(V):
        PermsTime -= time()
        perms = computePerms(colConstraint, R, Knowns=Paux[:,col])
        PermsTime += time()
        TotalPerms += len(perms)
        AddTimes -= time()
        s.add(Or( *(And( [P[i][col] if p else Not(P[i][col]) for (i,p) in enumerate(pm) if Paux[i,col] == -1]) for pm in perms) ))
        AddTimes += time()

    SetupTime += time()
    print(f"{TotalPerms}", end=" ")
    SolveTime -= time()

    if s.check() == sat:
        SolveTime += time()
        m = s.model()
        WellPosedTime -= time()
        s.add(Or( *(Not(P[i][j]) for j in range(C) for i in range(R) if m[P[i][j]]) ))
        sol1 = '\n'.join(['|' + '|'.join(['X' if m[P[i][j]] else ' ' for j in range(C)]) + '|' for i in range(R)])
        if s.check() == sat:
            WellPosedTime += time()
            m = s.model()
            sol2 = '\n'.join(['|' + '|'.join(['X' if m[P[i][j]] else ' ' for j in range(C)]) + '|' for i in range(R)])
            # print(f"The problem is not well-posed: it has more than one solution:\n{sol1}\nand\n{sol2}")
            return (False,None)
        WellPosedTime += time()
        # print(f"The problem is well-posed! Solution:\n{sol1}")
        return (True,sol1)     

    else:
        SolveTime += time()
        # print('The problem is not well-posed: it has no solution!')
        return (False,None)
    


if __name__ == "__main__":

    for sz in range(5,31,5):
        # for H,V in generateNonograms(sz,N=5):
        for i in range(1,6):
            H,V = readPuzzle(f"{sz}_{sz}_{i}")
            PermsTime = 0
            SolveTime = 0
            SetupTime = 0
            AddTimes = 0
            WellPosedTime = 0
            TotalPerms = 0
            print(f"{sz}", end=" ")
            TotalTime = -time()
            (_, sol1) = nonogram(V, H)
            TotalTime += time()
            print(f"{TotalTime//1e3:.0f} {SolveTime//1e3:.0f} {SetupTime//1e3:.0f} {PermsTime//1e3:.0f} {AddTimes//1e3:.0f}",end=" ")
            assert sum(list(map(sum,H))) == sum(list(map(sum,V)))
            nBlocks = 0
            sumBlocks = 0
            for h in H:
                nBlocks += len(h)
                sumBlocks += sum(h)
            for v in V:
                nBlocks += len(v)
                sumBlocks += sum(v)
            AvgBlockSize = sumBlocks/nBlocks
            FilledCells = sum(list(map(sum,H)))
            print(f"{FilledCells:.0f} {AvgBlockSize:.2f}")
            continue
            PermsTime = 0
            SolveTime = 0
            SetupTime = 0
            AddTimes = 0
            WellPosedTime = 0
            TotalPerms = 0
            TotalTime = 0
            print(f"{sz}", end=" ")
            TotalTime = -time()
            (ret,sol2) = well_posed(V, H)
            TotalTime += time()
            print(f"{TotalTime//1e3:.0f} {SolveTime//1e3:.0f} {SetupTime//1e3:.0f} {PermsTime//1e3:.0f} {AddTimes//1e3:.0f}",end=" ")
            print(f"{WellPosedTime//1e3:.0f} {int(ret)}")
            if ret:
                assert(sol1 == sol2)


