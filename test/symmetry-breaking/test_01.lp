%*-----------------------------------------------------------------------------------------------------
Test designed for issue #87
    https://github.com/ssardina-research/cfond-asp-private/issues/87




-------------------------------------------------------------*%
#const numStates = 3.
state(0..numStates).
initialState(0).
goalState(numStates).

% VERSION 1: current
%  if I connects to non-goal J, then I or someone before I should connect to J-1
:- successor(I, J), not goalState(J), J > I, J > 1, {successor(K, J-1): state(K), state(J-1), K <= I} 0.

% VERSION 2: is it equivalent to the previous one? No, it is not!
% if I connects to non-goal J, then anything I or before I should NOT connect to J-1!!! Crazy, totally different!
% :- successor(I, J), not goalState(J), J > I, J > 1, state(K), state(J-1), K <= I, successor(K, J-1).

%*---------------------------------------------------------------------------------------------------------------
:::Strong solution: This is specified by three constraints.
---------------------------------------------------------------------------------------------------------------*%
terminates(X) :- goalState(X).
terminates(X) :- state(X), terminates(Y): successor(X, Y).
:- not terminates(X), state(X).



% this is SAT under V1 but UNSAT under V2!
% it should be sat, because while 0 is connected to 2, it is also connected to 1 = 2-1
successor(0, 1).
successor(0, 2).
successor(1, 2).
successor(2, 3).

#show successor/2.