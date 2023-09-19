%*---------------------------------------------------------------------------------------------------------------
ASP based encoding for computing a FOND controller, inspired by FondSat, fueled by Clingo.
---------------------------------------------------------------------------------------------------------------*%
#const istop  = "SAT".
#const imin   = 0.
#const imax   = 32.

#program base.
initialState(1).
state("goal").
goalState("goal").
reachableG("goal", 0).% S1

#program step(k).
state(k).
{policy(k, Action): action(Action)} = 1.

% try this with volatile query
0 {transition(k, Effect, NextState): state(NextState), policy(k, Action), actionEffect(Action, Effect) } 1 .
0 {transition(State, Effect, k): state(State), State < k, not goalState(State), policy(State, Action), actionEffect(Action, Effect) } 1 .


% :- {policy(k, A1): undo(A1, A2), policy(S2, A2), transition(k,"e1", S2)}!=0.
% :- {policy(S2, A1): undo(A1, A2), policy(k, A2), transition(S2,"e1", k)}!=0.

0 {holds(k,Variable,Value) : variableValue(Variable,Value)} 1 :- variable(Variable).

successor(k, Y) :- transition(k, _, Y).
successor(X, k) :- transition(X, _, k), X < k.

transitionEffect(k, Effect, k) :- transition(k, Effect, NextState).
transitionEffect(State, Effect, k) :- transition(State, Effect, k), State < k, not goalState(State).

:- policy(State, Action), actionEffect(Action, Effect), not transitionEffect(State, Effect, _), query(k).

% cannotExecute(k, Action) :- state(k), action(Action), {not holds(k, Variable, Value): precondition(Action, Variable, Value)}!=0. % E1
% -policy(k, Action) :- cannotExecute(k, Action). % E2

:- policy(k, Action), precondition(Action, Variable, Value), not holds(k, Variable, Value). % P1
% -holds(k, Variable, Value1):- policy(k, Action), precondition(Action, Variable, Value), variableValue(Variable, Value1), Value1 != Value. % P2


not holds(NextState, Variable, Value) :- NextState = k, transition(State, Effect, NextState), policy(State, Action), del(Action, Effect, Variable, Value). % N1
not holds(NextState, Variable, Value) :- NextState = k, not holds(State, Variable, Value), variableValue(Variable, Value), successor(State, NextState), {transition(State, Effect, NextState): policy(State, Action), NextState = k, add(Action, Effect, Variable, Value)} 0. % N2
not holds(NextState, Variable, Value) :- NextState = k, not holds(State, Variable, Value), variableValue(Variable, Value), policy(State, Action), numEffects(Action, N), N>1, transition(State, Effect1, NextState), not add(Action, Effect1, Variable, Value), add(Action, Effect2, Variable, Value), Effect1 != Effect2. %N3


not holds(NextState, Variable, Value) :- State = k, NextState != k, transition(State, Effect, NextState), policy(State, Action), del(Action, Effect, Variable, Value). % N1
not holds(NextState, Variable, Value) :- State = k, NextState != k, not holds(State, Variable, Value), variableValue(Variable, Value), successor(State, NextState), {transition(State, Effect, NextState): policy(State, Action), State = k, NextState != k,  add(Action, Effect, Variable, Value)} 0. % N2
not holds(NextState, Variable, Value) :- State = k, NextState != k, not holds(State, Variable, Value), variableValue(Variable, Value), policy(State, Action), numEffects(Action, N), N>1, transition(State, Effect1, NextState), not add(Action, Effect1, Variable, Value), add(Action, Effect2, Variable, Value), Effect1 != Effect2. %N3


:- mutexGroup(Group), not {holds(k, Variable, Value) : mutex(Group, Variable, Value)} 1.

% symmetry breaking
sibling(k, Y) :- successor(Z, k), successor(Z, Y), k != Y.
sibling(X, k) :- successor(Z, X), successor(Z, k), X != k.

:- precedence(E1, E2), J1=k, transition(S, E1, J1), J1>S, 1 {transition(S, E2, J2): J2<J1, J2>S, not goalState(J2)}. % S4

-successor(K, J) :- successor(I, J), J= k, not sibling(K, I), J > 2, not goalState(J), state(K), 1 < K < I. % S1
:- successor(I, J), J=k, I<k, not goalState(I), J>2, {successor(K, J-1):state(K), state(J-1), K <= I} 0. % S2

#program check(k).
{state(K): state(K)}>2 :- query(k).

reachableG(State, k) :- successor(State, NextState), reachableG(NextState, _),  query(k).  % S2
:- not reachableG(State, _), state(State),  query(k).  % S3



% #show transition/3.
% #show holds/3.
% #show policy/2.
% #show state/1.
% #show reachableG/1.
#show successor/2.