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
:::GENERATION: A Policy is a tuple (State, Action). There should be one tuple per state, except for the goal state.

Action: An action is the name of a domain action. For example, "pick-from-table(b1)". An example of a policy tuple is (0, "pick-from-table(b1)").
---------------------------------------------------------------------------------------------------------------*%
{policy(State, Action): action(Action)} = 1 :- state(State), not goalState(State).

%*---------------------------------------------------------------------------------------------------------------
:::GENERATION: A transition is a tuple (State, Effect, State), such that (State, Action) is in the policy, and Effect is an effect if the given action.

For a tuple (S, A) in the policy, generate Z transitions (S, E, S') where Z is the number of effects of action A.

Nondeterministic planning actions are determinised by adding a suffix.
For example, the non-deterministic action put-on-block(b1, b2) has two nondeterministic effects.
The determinisation produces two actions:
1. put-on-block_det_0(b1, b2), and
2. put-on-block_det_1(b1, b2).

In the ASP instance, we associate the action put-on-block(b1, b2) with two effects: e1 and e2.
Effects e1 and e2 correspond to the effect of actions put-on-block_det_0(b1, b2) and put-on-block_det_1(b1, b2), respectively.

In general, an action with suffix _det_{i} will correspond to effect e{i+1} in our model. A deterministic planning action always has one effect, labelled as e1.
---------------------------------------------------------------------------------------------------------------*%
{transition(State, Effect, NextState): state(NextState),  maxND(L), NextState <= (State+1) * L} = 1 :-
    policy(State, Action), actionEffect(Action, Effect).


%*---------------------------------------------------------------------------------------------------------------
::: holds(State, Variable, Value): Variable must have value Value in state State.

This implements a PRP-like regression/weakest-precondition approach, by regessing from the goal condition on what must be true in each controller state.

HF. A variable cannot have 2 different values in a state.
P1. Preconditions must be forced when an action is executed in a controller State
    Action precondition: (n, a) -> p(n) if p in prec(a)
---------------------------------------------------------------------------------------------------------------*%
:- holds(State, Variable, Value1), holds(State, Variable, Value2), Value1 != Value2. % HF
holds(State, Variable, Value) :- policy(State, Action), precondition(Action, Variable, Value). % P1

%%% REGRESSION IMPLEMENTATION --------------------------------
% :- policy(S1, A), del(A, E, P), next(S1, E, S2), holds(S2, P).
-holds(NextState, Variable, Value) :-   % N1 ## cannot be integrity constraint
    transition(State, Effect, NextState),
    policy(State, Action),
    del(Action, Effect, Variable, Value).
holds(State, Variable, Value) :-
    holds(NextState, Variable, Value),
    transition(State, Effect, NextState),
    {policy(State, Action): add(Action, Effect, Variable, Value)} 0.


%*---------------------------------------------------------------------------------------------------------------
:::Symmetry breaking based on directed graphs.
    Symmetry breaking puts constraints on how nodes are connected.
    The constraint is (ni , nj ) -> k≤i \/ (nk , nl), where j > 1, l=j-1, and ni , nj , nl are not goal states.
    Intuition is that a state ni should connect to ni+l only if states nj where j ≤ i are unavailable.

- succesor(X,Y): Y is a succesor of X if there is a transition from X to Y.

Note: The symmetry breaking produces a labelling as per breadth first search.
S2. If J is a successor of I, then all states K, where K <= I, should not have connection to J-1.
S3. Siblings should obey lexicographic ordering (two siblings version)
S4. Siblings should obey lexicographic ordering (more than two siblings version)
---------------------------------------------------------------------------------------------------------------*%
successor(X, Y) :- transition(X, _, Y).

:- successor(I, J), not goalState(J), J > I, J > 1, {successor(K, J-1): state(K), state(J-1), K <= I} 0. % S2

:- maxND(N), N<3, precedence(E1, E2), transition(S, E1, J1), J1 > S, not goalState(J1), 1 {transition(S, E2, J2): J2<J1, J2>S, not goalState(J2)}. % S3
:- maxND(N), N>2, precedence(E1, E2), transition(S, E1, J1), transition(S, E2, J2), S < J2 < J1, not goalState(J1), {transition(S, E3, J2): precedence(E3, E2), not goalState(J2)} = 0. % S4


%*---------------------------------------------------------------------------------------------------------------
:::Mutex (derived from SAS encoding). In any state, there should be at most one mutually exclusive variable value pairs.
---------------------------------------------------------------------------------------------------------------*%
:- mutexGroup(Group), state(State), not {holds(State, Variable, Value) : mutex(Group, Variable, Value)} 1.

%*---------------------------------------------------------------------------------------------------------------
:::Strong cyclic solution: Goal should be reachable from all states. This is specified by three constraints.

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

