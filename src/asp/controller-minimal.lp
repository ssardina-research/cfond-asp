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
:- precedence(E1, E2), transition(S, E1, J1), J1>S, not goalState(J1), 1 {transition(S, E2, J2): J2<J1, J2>S, not goalState(J2)}. % S4

-holds(NextState, Variable, Value) :- transition(State, Effect, NextState), policy(State, Action), del(Action, Effect, Variable, Value). % N1

-holds(NextState, Variable, Value) :- -holds(State, Variable, Value), variableValue(Variable, Value), transition(State, Effect, NextState), {transition(State, Effect, NextState): policy(State, Action), add(Action, Effect, Variable, Value)} 0. % N2

% -holds(NextState, Variable, Value) :- -holds(State, Variable, Value), variableValue(Variable, Value), successor(State, NextState), transition(State, Effect, NextState), policy(State, Action), not add(Action, Effect, Variable, Value). % N2


% -holds(NextState, Variable, Value) :- -holds(State, Variable, Value), variableValue(Variable, Value), policy(State, Action), numEffects(Action, N), N>1, transition(State, Effect1, NextState), not add(Action, Effect1, Variable, Value), add(Action, Effect2, Variable, Value), Effect1 != Effect2. %N3

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

% #heuristic policy(State, Action). [2, factor]
% #heuristic holds(State, Variable, Value). [2, factor]
% #heuristic policy(State, Action). [2, factor]
% #heuristic  holds(State-1, Variable, Value) : holds(State, Variable, Value).  [5*numStates - State +1, true]