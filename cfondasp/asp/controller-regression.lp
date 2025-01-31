%*---------------------------------------------------------------------------------------------------------------
ASP based encoding for computing a FOND controller, inspired by REGRESSION/PRP, fueled by Clingo.
---------------------------------------------------------------------------------------------------------------*%

%*---------------------------------------------------------------------------------------------------------------
::: numStates (input). Upper bound on the number of states in a controller.
The total number of states in a controller will be numStates + 1.
---------------------------------------------------------------------------------------------------------------*%
#const numStates = 2.

%*---------------------------------------------------------------------------------------------------------------
:::DEFINITION: State
A controller state is modelled by terms state(0), state(1), ..., state(n) where n is the upper bound (i.e., numStates).
State 0 is reserved for the initial state and the highest number (i.e., numStates) is reserved for the goal state.
---------------------------------------------------------------------------------------------------------------*%
state(0..numStates).

% Set 0 as the initial state
initialState(0).

% set numStates as the goal state.
goalState(numStates).

%*---------------------------------------------------------------------------------------------------------------
:::GENERATION of action at controller states

    1) policy(State, Action): an action is done in each state (except at goal state)
    2) transition(State, Effect, NextState): State transitions to NextState under the Effect-th (of action at State)
        For a tuple (S, A) in the policy, generate Z transitions (S, E, S') where Z = number of effects of action A.


    Action: An action is the name of a domain action. For example, "pick-from-table(b1)".
        An example of a policy tuple is (0, "pick-from-table(b1)").

    Nondeterministic planning actions are determinised by adding a suffix.
    For example, the non-deterministic action put-on-block(b1, b2) has two nondeterministic effects.
    The determinisation produces two actions:
    1. put-on-block_det_0(b1, b2), and
    2. put-on-block_det_1(b1, b2).

    In the ASP instance, we associate the action put-on-block(b1, b2) with two effects: e1 and e2.
    Effects e1 and e2 correspond to the effect of put-on-block_det_0(b1, b2) and put-on-block_det_1(b1, b2), resp.

    In general, an action with suffix _det_{i} will correspond to effect e{i+1} in our model.
    A deterministic planning action always has one effect, labelled as e1.
---------------------------------------------------------------------------------------------------------------*%
{policy(State, Action): action(Action)} = 1 :- state(State), not goalState(State).

{transition(State, Effect, NextState): state(NextState),  maxND(L), NextState <= (State+1) * L} = 1 :-
    policy(State, Action), actionEffect(Action, Effect).


%*---------------------------------------------------------------------------------------------------------------
:::Auxiliary atoms based on transitions.

- successor(X, Y): Y is a successor of X if there is a transition from X to Y.
- sibling(X, Y): X and Y are two successor of the same parent, that is, two effects of the same action execution
---------------------------------------------------------------------------------------------------------------*%
successor(X, Y) :- transition(X, _, Y).
sibling(X, Y) :- successor(Z, X), successor(Z, Y), X != Y.


%*---------------------------------------------------------------------------------------------------------------
::: holds(State, Variable, Value): Variable must have value Value in state State.
--------------------------------------------------------------------------------------------------------------*%
% A variable cannot have 2 different values in a state.
:- holds(State, Variable, Value1), holds(State, Variable, Value2), Value1 != Value2.

% P1. Preconditions must be forced when an action is executed in a controller State
holds(State, Variable, Value) :- policy(State, Action), precondition(Action, Variable, Value).

%%% REGRESSION IMPLEMENTATION --------------------------------
% Forward propagation of negative effects
-holds(NextState, Variable, Value) :-
    transition(State, Effect, NextState),
    policy(State, Action),
    del(Action, Effect, Variable, Value).

% REGRESSION: backward propagation of positive effects
% This implements a PRP-like regression/weakest-precondition approach, by regression from the goal condition
%     on what must be true in each controller state.
%   if Variable = Value in NextState, and action does not set it, then it has to be true already in State
holds(State, Variable, Value) :-
    holds(NextState, Variable, Value),
    transition(State, Effect, NextState),
    {policy(State, Action): add(Action, Effect, Variable, Value)} 0.


%*---------------------------------------------------------------------------------------------------------------
:::SYMMETRY BREAKING BASED ON DIRECTED GRAPHS.
    Symmetry breaking puts constraints on how nodes are connected.
    The constraint is (ni , nj ) -> k≤i \/ (nk , nl), where j > 1, l=j-1, and ni , nj , nl are not goal states.
    Intuition is that a state ni should connect to ni+l only if states nj where j ≤ i are unavailable.

Note: The symmetry breaking produces a labelling as per breadth first search.
---------------------------------------------------------------------------------------------------------------*%

% S1. If J is a successor of I, then all non-sibling states K, where K < I, cannot connect to J.
% Left out; seems to be making it slower
% -successor(K, J) :- successor(I, J), not sibling(K, I), J > I, not goalState(J), state(K), 1 < K < I.

% S2. If I connects to non-goal J, there must be some K <= I that connects to J-1 (we don´t skip states)
:- successor(I, J), not goalState(J), J > I, J > 1, {successor(K, J-1): state(K), state(J-1), K <= I} 0.

% S3. siblings effects should obey lexicographic ordering (two siblings version)
% :- maxND(N), N < 3, precedence(E1, E2), transition(S, E1, J1), S1 > S, not goalState(S1),
%     1 {transition(S, E2, S2): S1 > S2 > S, not goalState(S2)}.

% should be equivalent to move precedence to the cardibality constraint right where it is used, right?
% :- maxND(N), N < 3, transition(S, E1, J1), S1 > S, not goalState(S1),
%     1 {transition(S, E2, S2): precedence(E1, E2), S1 > S2 > S, not goalState(S2)}.

% this integrity constraint should be equivalent? but a bit slower?
:- maxND(N), N < 3, transition(S, E1, S1), S1 > S, not goalState(S1),
    precedence(E1, E2), transition(S, E2, S2), S < S2 < S1.

% S4. Siblings should obey lexicographic ordering (more than two siblings version)
:- maxND(N), N > 2, precedence(E1, E2), transition(S, E1, J1), transition(S, E2, J2), S < J2 < J1, not goalState(J1),
     {transition(S, E3, J2): precedence(E3, E2), not goalState(J2)} = 0.

%*---------------------------------------------------------------------------------------------------------------
:::MUTEX (derived from SAS encoding).

In any state, there should be at most one mutually exclusive variable value pairs.
---------------------------------------------------------------------------------------------------------------*%
:- mutexGroup(Group), state(State), not {holds(State, Variable, Value) : mutex(Group, Variable, Value)} 1.

%*---------------------------------------------------------------------------------------------------------------
:::STRONG CYCLIC SOLUTION: Goal should be reachable from all states. This is specified by three constraints.

S1. Goal is reachable from the goal state.
S2. If goal is reachable from a state Y, then goal is reachable from all states X, such that Y is a successor of X.
S3. It should not be the case that there is a state from where goal is unreachable.
---------------------------------------------------------------------------------------------------------------*%
reachableG(State) :- goalState(State).  % S1
reachableG(State) :- successor(State, NextState), reachableG(NextState).  % S2
:- not reachableG(State), state(State).  % S3

%*---------------------------------------------------------------------------------------------------------------
:::OUTPUT. Show transition, holds, and policy.
---------------------------------------------------------------------------------------------------------------*%
#show transition/3.
#show holds/3.
#show policy/2.

