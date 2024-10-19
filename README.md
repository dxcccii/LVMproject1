                                  8I                                                         
                                  8I                                                         
                                  8I                                               gg    gg  
                                  8I                                               ""    ""  
                            ,gggg,8I     ,gg,   ,gg   ,gggg,    ,gggg,    ,gggg,   gg    gg  
                           dP"  "Y8I    d8""8b,dP"   dP"  "Yb  dP"  "Yb  dP"  "Yb  88    88  
                          i8'    ,8I   dP   ,88"    i8'       i8'       i8'        88    88  
                         ,d8,   ,d8b,,dP  ,dP"Y8,  ,d8,_    _,d8,_    _,d8,_    __,88,__,88,_
                        P"Y8888P"Y88"  dP"   "Y88P""Y8888PPP""Y8888PPP""Y8888PP8P""Y88P""Y8 
                                                            
             IST // MATHEMATICS AND COMPUTATION // LOGIC AND MODEL CHECKING // BY GROUP 7 // 113215 & 90178
__________________________________________________________________________________________________________________________
                           _
                          | |                                                                        |            
       o   _  _  _     _  | |  _   _  _  _    _   _  _  _|_  __, _|_  o  __   _  _      __   ,_    __|   _   ,_   
       |  / |/ |/ |  |/ \_|/  |/  / |/ |/ |  |/  / |/ |  |  /  |  |  |  /  \_/ |/ |    /  \_/  |  /  |  |/  /  |  
       |_/  |  |  |_/|__/ |__/|__/  |  |  |_/|__/  |  |_/|_/\_/|_/|_/|_/\__/   |  |_/  \__/    |_/\_/|_/|__/   |_/
                    /|                                                                                            
                    \| 
 __________________________________________________________________________________________________________________________

Regarding python scripts and their different iterations:

The order in which they should be checked and evaluated (and the order they were 
implemented) is as such:

1) project1nonogram.py
2) project1nonogramFinal.py
3) project1nonogramFinalOptimized.py

__________________________________________________________________________________________________________________________
                                                       
                             o                        |              o             
                                 _  _ _|_  ,_   __  __|         ___|_   __  _  _   
                             |  / |/ | |  /  | /  \/  |  |   | /   | | /  \/ |/ |  
                             |_/  |  |_/_/   |_|__/\_/|_/ \_/|_|___/_/_|__/  |  |_/
__________________________________________________________________________________________________________________________

 A Nonogram is a logic-based puzzle that involves filling in a grid according to numerical clues given
for each row and column. These clues specify the lengths of sequences of consecutive black squares,
with at least one blank square between each sequence. The objective is to uncover a hidden picture
that satisfies the constraints presented in the clues, and a well-posed Nonogram has a unique solution.

The goal of this project is to encode a Nonogram puzzle as a SAT problem, translating its constraints
into a Boolean formula that can be processed by the Z3 solver.

A key component of the solver is the Conflict-Driven Clause Learning (CDCL) algorithm. CDCL
builds upon the basic DPLL (Davis-Putnam-Logemann-Loveland) procedure by using a more dynamic
approach to decision-making. As the solver explores possible assignments for literals, it detects conflicts
that arise from inconsistent assignments, learns new clauses from these conflicts, and backtracks
intelligently, learning clauses from the conflicts and adds new constraints to avoid further conflicts,
thereby guiding it more effectively toward a solution.

The first part of this report presents an example of the CDCL algorithm applied to a formula,
illustrating the process of assigning values to literals, identifying conflicts, and learning new clauses.
This example serves as an introduction to the underlying mechanism of the solver, setting the stage
for the subsequent application to Nonograms.       
