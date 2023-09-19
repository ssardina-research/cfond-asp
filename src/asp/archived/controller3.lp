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

% 1 {transition(State, Action, NextState): state(NextState)} 1 :- policy(State, Action).
1 {transition(State, Action, NextState): state(NextState), maxND(Z), NextState <= (State+1) * Z, NextState <= numStates} 1 :- policy(State, Action).
% 1 {transition(State, Action, NextState): state(NextState), actionType(ActionType, Action), numEffects(ActionType, Z), NextState <= State * Z + Z+1, NextState <= numStates} 1 :- policy(State, Action).


0 {holds(State,Variable,Value) : variableValue(Variable,Value)} 1 :- state(State), variable(Variable).


successor(X, Y) :- transition(X, _, Y).


:- state(State), action(Action), not 0 {transition(State, Action, _)} 1.  % T1
:- policy(State, Action1), sibling(Action1, Action2), not policy(State, Action2). % S1

% % Symmetry
:- successor(I, J), not goalState(J), J>1, {successor(K, J-1):state(K), state(J-1), K <= I} 0.
% :- state(I), state(J), not goalState(I), not goalState(J), J>1, successor(I, J), {successor(K, J-1):state(K), state(J-1), not goalState(J-1), K <= I} 0.


:- transition(S, A1, J1), J1>S, not goalState(J1), 1 {transition(S, A2, J2): J2<J1, J2>S, not goalState(J2)}, precedence(A1, A2).

:- policy(State, Action), precondition(Action, Variable, Value), not holds(State, Variable, Value).
- holds(State, Variable, Value1):- policy(State, Action), precondition(Action, Variable, Value), variableValue(Variable, Value1), Value1 != Value.

not holds(NextState, Variable, Value) :- transition(_, Action, NextState), del(Action, Variable, Value). % N1
not holds(NextState, Variable, Value) :- not holds(State, Variable, Value), variableValue(Variable, Value), successor(State, NextState), {transition(State, Action, NextState): add(Action, Variable, Value)} 0. % N2
not holds(NextState, Variable, Value) :- not holds(State, Variable, Value), variableValue(Variable, Value), transition(State, Action, NextState), not add(Action, Variable, Value), sibling(Action, SiblingAction), add(SiblingAction, Variable, Value).

:- mutexGroup(Group), state(State), not {holds(State, Variable, Value) : mutex(Group, Variable, Value)} 1.


reachableG(State) :- goalState(State).  % S1
reachableG(State) :- successor(State, NextState), reachableG(NextState).  % S2
:- not reachableG(State), state(State).  % S3



% #show metaPolicy/2.
#show transition/3.
#show holds/3.

% % % % #show policy/2.
% % % % #show reachableG/2.

