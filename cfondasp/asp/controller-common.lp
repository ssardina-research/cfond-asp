%*---------------------------------------------------------------------------------------------------------------
ASP based encoding for computing a FOND controller - COMMON CODE TO MANY SOLVERS
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
:::Auxiliary derived atoms

    These are used by other rules
--------------------------------------------------------------------------------------------------------------*%
% Y is a successor of X if there is a transition from X to Y.
successor(X, Y) :- transition(X, _, Y).

% X and Y are two successor of the same parent, that is, two effects of the same action execution
sibling(X, Y) :- successor(Z, X), successor(Z, Y), X != Y.

% state S1 has used by (connected from) some state before S2
usedBefore(S1, S2) :- state(S1), state(S2), successor(S, S1), S < S2.

% transitive clousure on precedence/2: effect E1 is before E2
precedenceStar(E1, E2) :- precedence(E1, E2).
precedenceStar(E1, E2) :- precedence(E1, E3), precedenceStar(E3, E2).

%*---------------------------------------------------------------------------------------------------------------
:::SYMMETRY BREAKING BASED ON DIRECTED GRAPHS.
    Symmetry breaking puts constraints on how nodes are connected/allocated.

    1. If we connect state N from K, either K or someone before K has already used (connected to) N-1
    2. Within an action, when using fresh new states, we connect effect E1 before E2 if E1 is a predecessor of E2.
        - E2 can come before E1 if E2 is reusing some previous effect transition.
            Say E1 --> 50, E2 --> 51, E3 --> 50 (that is OK bc E3 is reusing 50 used by E1)
        - Also, enforce this if the next states are NEW fresh states (not used by previous controller states)
---------------------------------------------------------------------------------------------------------------*%

% S1. If J is a successor of I, then all non-sibling states K, where K < I, cannot connect to J.
% Left out; seems to be making it slower
% -successor(K, J) :- successor(I, J), not sibling(K, I), J > I, not goalState(J), state(K), 1 < K < I.

% S2. NO SKIP STATES - If I connects to non-goal J, there must be some K <= I that connects to J-1
:- successor(I, J), not goalState(J), J > I, J > 1, {successor(K, J-1): state(K), state(J-1), K <= I} 0.

% S3. ORDER EFFECTS: siblings effects should obey lexicographic ordering (two siblings version)
% S3.1. Special case for ND of 2 (allocate E1 before E2)
:- maxND(2), transition(S, E1, S1), not goalState(S1),
    precedence(E1, E2), transition(S, E2, S2), S < S2 < S1, % order broken E2 before E1!
    not usedBefore(S1, S), not usedBefore(S2, S). % next states not used before S (fresh S1 and S2!)
% S3.2. General case for any number of ND
:- precedence(E1, E2), transition(S, E1, S1), transition(S, E2, S2),
    S > S2 > S1, % effect ordering broken - E1 connects further away than E2!
    not usedBefore(S1, S), not usedBefore(S2, S), % next states not used before S (fresh S1 and S2!)
    not goalState(S1), % hence S2 wont be goal state either as it is lower in the order
    {transition(S, E3, S2): precedenceStar(E3, E2)} = 0. % E2 is re-using an effect-successor


%*---------------------------------------------------------------------------------------------------------------
:::MUTEX (derived from SAS encoding).

In any state, there should be at most one mutually exclusive variable value pairs.
---------------------------------------------------------------------------------------------------------------*%
:- mutexGroup(Group), state(State), not {holds(State, Variable, Value) : mutex(Group, Variable, Value)} 1.
