%*---------------------------------------------------------------------------------------------------------------
ASP based encoding for computing a FOND controller, inspired by FondSat
---------------------------------------------------------------------------------------------------------------*%

%*---------------------------------------------------------------------------------------------------------------
- numStates (input). Upper bound on the number of states in a controller.

State 0 is reserved for the initial state and the highest number (i.e., numStates) is reserved for the goal state.
The total number of states in a controller will be numStates + 1.
---------------------------------------------------------------------------------------------------------------*%
#const numStates = 2.


% State declaration. This creates terms state(0), state(1), ..., state(n) where n is the upper bound (i.e., numStates).
state(0..numStates).

% Set 0 as the initial state
initialState(0).

% set numStates as the goal state.
goalState(numStates).

% Gen
{metaPolicy(State, ActionType): actionType(ActionType)}=1 :- state(State), not goalState(State).

{policy(State, Action): actionType(ActionType, Action)}=Z :- metaPolicy(State, ActionType), numEffects(ActionType, Z).

1 {transition(State, Action, NextState): state(NextState)} 1 :- policy(State, Action).
% 1 {transition(State, Action, NextState): state(NextState), maxND(Z), NextState <= (State+1) * Z, NextState <= numStates} 1 :- policy(State, Action).
% 1 {transition(State, Action, NextState): state(NextState), actionType(ActionType, Action), numEffects(ActionType, Z), NextState <= State * Z + Z+1, NextState <= numStates} 1 :- policy(State, Action).

:- goalState(State), {transition(State, Action, NextState)} !=0 .

0 {holds(State,Variable,Value) : variableValue(Variable,Value)} 1 :- state(State), variable(Variable).


successor(X, Y) :- transition(X, _, Y).


:- state(State), action(Action), not 0 {transition(State, Action, _)} 1.  % T1
:- policy(State, Action1), sibling(Action1, Action2), not policy(State, Action2). % S1

% new
:- transition(State, Action, NextState), not policy(State, Action).

% % Symmetry
% - successor(K, J) :- successor(I, J), J > I, not goalState(J), state(K), 1 < K < I.

% :- successor(I, J), not goalState(J), J>1, {successor(K, J-1):state(K), state(J-1), K <= I} 0.
:- successor(I, J), backboneState(I), not backboneState(J-1), I >0, J>1, {successor(K, J-1): backboneState(K), state(J-1), K <= I} 0.

% :- precedence(A1, A2), transition(S, A1, J1), J1>S, not goalState(J1), 1 {transition(S, A2, J2): J2<J1, J2>S, not goalState(J2)}.
% % - transition(S, A2, J2) :- precedence(A1, A2), not goalState(J1), not goalState(J2), state(J2), transition(S, A1, J1), J1 > S, J2 > S, 1 < J2 < J1.

:- policy(State, Action), precondition(Action, Variable, Value), not holds(State, Variable, Value).
- holds(State, Variable, Value1):- policy(State, Action), precondition(Action, Variable, Value), variableValue(Variable, Value1), Value1 != Value.

not holds(NextState, Variable, Value) :- transition(_, Action, NextState), del(Action, Variable, Value). % N1
not holds(NextState, Variable, Value) :- not holds(State, Variable, Value), variableValue(Variable, Value), successor(State, NextState), {transition(State, Action, NextState): add(Action, Variable, Value)} 0. % N2
not holds(NextState, Variable, Value) :- not holds(State, Variable, Value), variableValue(Variable, Value), transition(State, Action, NextState), not add(Action, Variable, Value), sibling(Action, SiblingAction), add(SiblingAction, Variable, Value).

:- mutexGroup(Group), state(State), not {holds(State, Variable, Value) : mutex(Group, Variable, Value)} 1.


reachableI(State) :- initialState(State).  % Initial state is reachable from start
reachableI(NextState) :- successor(State, NextState), reachableI(State).

reachableG(State) :- goalState(State).  % S1
reachableG(State) :- successor(State, NextState), reachableG(NextState).  % S2
:- reachableI(State), not reachableG(State).  % S3


% #show metaPolicy/2.
% #show transition/3.
% #show holds/3.

#show policy/2.
% % % % #show reachableG/2.

