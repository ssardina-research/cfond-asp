%*---------------------------------------------------------------------------------------------------------------
Linear Variable
---------------------------------------------------------------------------------------------------------------*%
linear(0).

%*---------------------------------------------------------------------------------------------------------------
Value Ordering.
0: Atom position(p0)
1: Atom position(p1)
2: Atom position(p10)
3: Atom position(p11)
4: Atom position(p12)
5: Atom position(p13)
6: Atom position(p14)
7: Atom position(p15)
8: Atom position(p2)
9: Atom position(p3)
10: Atom position(p4)
11: Atom position(p5)
12: Atom position(p6)
13: Atom position(p7)
14: Atom position(p8)
15: Atom position(p9)
---------------------------------------------------------------------------------------------------------------*%
order(0,0,1).
order(0,1,8).
order(0,8,9).
order(0,9,10).
order(0,10,11).
order(0,11,12).
order(0,12,13).
order(0,13,14).
order(0,14,15).
order(0,15,2).
order(0,2,3).
order(0,3,4).
order(0,4,5).
order(0,5,6).
order(0,6,7).
%%%%
order(V, Y, X) :- order(V, X, Y). 
order(V, X, X) :- order(V, X, Y). 

%*---------------------------------------------------------------------------------------------------------------
Constraints
---------------------------------------------------------------------------------------------------------------*%
:- holds(State, Variable, Value1), linear(Variable), state(State), not goalState(State), {successor(State, NextState): holds(NextState, Variable, Value2), variableValue(Variable, Value2), order(Variable, Value1, Value2)} 0.
% :- holds(State, Variable, Value1), linear(Variable), state(State), not goalState(State), {successor(State, NextState): holds(NextState, Variable, Value2), variableValue(Variable, Value2), not order(Variable, Value1, Value2)}!=0.