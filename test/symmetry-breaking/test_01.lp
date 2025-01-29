#const numStates = 3.
state(0..numStates).
initialState(0).
goalState(numStates).

{successor(State, NextState): state(NextState)}=1 :- state(State), not goalState(State).

% current
:- successor(I, J), not goalState(J), J>I, J>1, {successor(K, J-1):state(K), state(J-1), K <= I} 0. % S2

% should be equivalent
% :- successor(I, J), not goalState(J), J > I, J > 1, state(K), state(J-1), K <= I, successor(K, J-1).

%*---------------------------------------------------------------------------------------------------------------
:::Strong solution: This is specified by three constraints.
---------------------------------------------------------------------------------------------------------------*%
terminates(X) :- goalState(X).
terminates(X) :- state(X), terminates(Y): successor(X, Y).
:- not terminates(X), state(X).


%% successor(0,2) should not be allowed because 0 can connect to 1

% successor(0,2).
#show successor/2.