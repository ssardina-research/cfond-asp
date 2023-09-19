#const numStates = 2.
state(0..numStates).
initialState(0).
goalState(numStates).

{policy(State, Action): action(Action)} = 1 :- state(State), not goalState(State).
{transition(State, Effect, NextState): state(NextState),  maxND(L), NextState <= (State+1) * L}=1 :- policy(State, Action), actionEffect(Action, Effect).
successor(X, Y) :- transition(X, _, Y).

:- holds(State, Variable, Value1), holds(State, Variable, Value2), Value1 != Value2.
holds(State, Variable, Value) :- policy(State, Action), precondition(Action, Variable, Value).

:- successor(I, J), not goalState(J), J>I, J>1, {successor(K, J-1):state(K), state(J-1), K <= I} 0. % S2
:- precedence(E1, E2), transition(S, E1, J1), transition(S, E2, J2), S < J2 < J1, not goalState(J1), {transition(S, E3, J2): precedence(E3, E2), not goalState(J2)}=0. % S5

% :- policy(S1, A), del(A, E, P), next(S1, E, S2), holds(S2, P).
-holds(NextState, Variable, Value) :- transition(State, Effect, NextState), policy(State, Action), del(Action, Effect, Variable, Value). % N1 ## cannot be integrity constraint

holds(State, Variable, Value) :- holds(NextState, Variable, Value),  transition(State, Effect, NextState),  {policy(State, Action): add(Action, Effect, Variable, Value)}0. 

:- mutexGroup(Group), state(State), not {holds(State, Variable, Value) : mutex(Group, Variable, Value)} 1.

reachableG(State) :- goalState(State).  % S1
reachableG(State) :- successor(State, NextState), reachableG(NextState).  % S2
:- not reachableG(State), state(State).  % S3

%*---------------------------------------------------------------------------------------------------------------
:::Output. Show transition, holds, and policy.
---------------------------------------------------------------------------------------------------------------*%
#show transition/3.
#show holds/3.
#show policy/2.

