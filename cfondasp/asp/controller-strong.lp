%*---------------------------------------------------------------------------------------------------------------
ASP based encoding for computing a FOND controller, inspired by FondSat, fueled by Clingo.
---------------------------------------------------------------------------------------------------------------*%

%*---------------------------------------------------------------------------------------------------------------
- numStates (input). Upper bound on the number of states in a controller.
The total number of states in a controller will be numStates + 1.
---------------------------------------------------------------------------------------------------------------*%
#const numStates = 2.

%*---------------------------------------------------------------------------------------------------------------
:::DEFINITION: STATE

A controller state is modelled by terms state(0), state(1), ..., state(n) - n is upper bound (i.e., numStates).
    State 0 is reserved for the initial state
    Highest number numStates is reserved for the goal state.
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
:::GENERATION: The term holds(S, Var, Val) implies that variable Var has value Val in state S.

The constraint only allows at most one value per variable per state.
The encoding only propagates negative effects, hence it is upto the solver to set the positive values of variables.
Note:- This is constrained by preconditions of actions (see the constraint on action precondition).
Note:- This may not be required, but it speeds up solving.
---------------------------------------------------------------------------------------------------------------*%
0 {holds(State, Variable, Value) : variableValue(Variable, Value)} 1 :- state(State), variable(Variable).

%*---------------------------------------------------------------------------------------------------------------
:::CONSTRAINTS: Action precondition: (n, a) -> p(n) if p in prec(a)

P1. If a tuple (S, A) is in the policy and a variable Var has value Val in action A's precondition
    then it should not be the case that Var does not have value Val in state S.
---------------------------------------------------------------------------------------------------------------*%
% NOTE: this integrity constraint, together witht he GENERATION CHOICE rule above allows infer holds/3
:- policy(State, Action), precondition(Action, Variable, Value), not holds(State, Variable, Value).

% NOTE: this should be equivalent? seems to run a bit slower (10s vs 8s)
% holds(State, Variable, Value) :- policy(State, Action), precondition(Action, Variable, Value).

%*---------------------------------------------------------------------------------------------------------------
::: SYMMETRY BREAKING BASED ON DIRECTED GRAPHS.

    Symmetry breaking puts constraints on how nodes are connected.
    Intuition is that a state ni should connect to ni+l only if states nj where j ≤ i are unavailable.
    The constraint is (ni , nj ) -> k ≤ i \/ (nk , nl), where j > 1, l = j-1, and ni, nj , nl are not goal states.
---------------------------------------------------------------------------------------------------------------*%
%  If J is a successor of I, then all non-sibling states K of I, that come before I (K < I), cannot connect to J.
-successor(K, J) :- successor(I, J), not sibling(K, I), J > I, not goalState(J), state(K), 1 < K < I. % S1

% If I connects to non-goal J, there must be some K <= I that connects to J-1 (we don´t skip states)
:- successor(I, J), not goalState(J), J > I, J > 1, {successor(K, J-1): state(K), state(J-1), K <= I} = 0.

%*---------------------------------------------------------------------------------------------------------------
::: PROPAGATION OF NEGATIVE CONDITIONS.

NOTE:: The use of not holds in implication increases the grounding speed but reduces the solving speed.
Replacing implication with integrity constraint reduces grounding and increases solving time considerably.
---------------------------------------------------------------------------------------------------------------*%
% N1. If an action deletes a value Val of a variable Var, then it should be the case that Var does not hold
%   value Val in the next state resulting from this action.
not holds(NextState, Variable, Value) :-
    transition(State, Effect, NextState), policy(State, Action), del(Action, Effect, Variable, Value).

% N2. If a variable Var does not hold a value Val in a state, then Var should not hold value Val in the next state
%   unless an action is done whose effect sets value of Var to Val.
not holds(NextState, Variable, Value) :-
    not holds(State, Variable, Value), variableValue(Variable, Value), successor(State, NextState),
    {transition(State, Effect, NextState): policy(State, Action), add(Action, Effect, Variable, Value)} 0.

% N3. If a variable Var does not hold a value Val in a state, then Var should not hold value Val in the next state
%   if an effect does not add it, but its sibling adds it.
%     This enforces that in this case the siblings yield a different state.
not holds(NextState, Variable, Value) :-
    not holds(State, Variable, Value), variableValue(Variable, Value),
    policy(State, Action), numEffects(Action, N), N > 1,
    transition(State, Effect1, NextState),
    not add(Action, Effect1, Variable, Value),
    add(Action, Effect2, Variable, Value), Effect1 != Effect2.

%*---------------------------------------------------------------------------------------------------------------
:::MUTEX (derived from SAS encoding).
    In any state, there should be at most one mutually exclusive variable value pairs.
---------------------------------------------------------------------------------------------------------------*%
:- mutexGroup(Group), state(State), not {holds(State, Variable, Value) : mutex(Group, Variable, Value)} 1.

%*---------------------------------------------------------------------------------------------------------------
:::STRONG SOLUTION: This is specified by three constraints.
---------------------------------------------------------------------------------------------------------------*%
terminates(X) :- goalState(X).
terminates(X) :- state(X), terminates(Y): successor(X, Y).
:- not terminates(X), state(X).

% NOTE: these are not equivalent to the 2nd rule above!
% they will support the derivation of terminatess(X) when it shouldn't!
% details: https://github.com/ssardina-research/cfond-asp-private/issues/74
% terminates(X) :- state(X), {not terminates(X) : successor(X, Y)} = 0.
% terminates(X) :- state(X), #count {Y : state(Y), not terminates(Y), successor(X, Y)} = 0.

%*---------------------------------------------------------------------------------------------------------------
:::Output. Show transition, holds, and policy.
---------------------------------------------------------------------------------------------------------------*%
#show transition/3.
#show holds/3.
#show policy/2.

% show for debugging as needed
% #show successor/2.
% #show terminates/1.