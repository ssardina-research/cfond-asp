%*---------------------------------------------------------------------------------------------------------------
ASP based encoding for computing a FOND controller, inspired by FONDSAT, fueled by Clingo.
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

This implements the FONDSAT approach by forcing preconditions and only propagating negative effects forward.

GENERATION G1: A variable can have zero or one value per state (i.e., at most one)

    The constraints N1-N3 will only propagate negative effects, hence it is upto the solver to freely set the positive values of variables as needed with G1.

    Note:- Note that this is constrained by preconditions of actions (see the constraint on action precondition).
    Note:- This may not be required, but it speeds up solving.

CONSTRAINTS:

P1. Preconditions must be forced when an action is executed in a controller State.
    Action precondition: (n, a) -> p(n) if p in prec(a)
    See we use an integrity constraint because it is faster than a rule deriving holds.
    This works ONLY because holds is justified via G1 generation rule; by itself it will not generate holds. See https://github.com/ssardina-research/cfond-asp-private/wiki/Controller:-Generating-holds-via-choice-rule-vs-constraints

N1-N3. Propagation of negative conditions.

N1. If an action deletes a value Val of a variable Var, then it should be the case that Var does not hold value Val in the next state resulting from this action.
N2. If a variable Var does not hold a value Val in a state, then Var should not hold value Val in the next state unless an action is done whose effect sets value of Var to Val.
N3. If a variable Var does not hold a value Val in a state, then Var should not hold value Val in the next state if an effect does not add it, but its sibling adds it.
    This enforces that in this case the siblings yield a different state.

NOTE:: The use of not holds in implication increases the grounding speed but reduces the solving speed. Replacing implication with integrity constraint reduces grounding and increases solving time considerably.
---------------------------------------------------------------------------------------------------------------*%
0 {holds(State,Variable,Value) : variableValue(Variable,Value)} 1 :- state(State), variable(Variable). % G1

:- policy(State, Action), precondition(Action, Variable, Value), not holds(State, Variable, Value). % P1 (faster than a rule for holds; works because of G1)

not holds(NextState, Variable, Value) :- % N1
    transition(State, Effect, NextState),
    policy(State, Action),
    del(Action, Effect, Variable, Value).
not holds(NextState, Variable, Value) :- % N2
    not holds(State, Variable, Value),
    variableValue(Variable, Value),
    successor(State, NextState),
    {transition(State, Effect, NextState): policy(State, Action), add(Action, Effect, Variable, Value)} 0.
not holds(NextState, Variable, Value) :- % N3
    not holds(State, Variable, Value),
    variableValue(Variable, Value),
    policy(State, Action),
    numEffects(Action, N), N>1,
    transition(State, Effect1, NextState),
    not add(Action, Effect1, Variable, Value),
    add(Action, Effect2, Variable, Value), Effect1 != Effect2.

%*---------------------------------------------------------------------------------------------------------------
::: Symmetry breaking based on directed graphs.
    Symmetry breaking puts constraints on how nodes are connected.
    The constraint is (ni , nj ) -> k≤i \/ (nk , nl), where j > 1, l=j-1, and ni , nj , nl are not goal states.
    Intuition is that a state ni should connect to ni+l only if states nj where j ≤ i are unavailable.

- succesor(X,Y): Y is a succesor of X if there is a transition from X to Y.
- sibling(X, Y): X and Y are siblings if they share a parent.

Note: The symmetry breaking produces a labelling as per breadth first search.
S1. If J is a successor of I, then all non-sibling states K, where K < I, cannot connect to J.
S2. If J is a successor of I, then all states K, where K <= I, should not have connection to J-1.
S3. Siblings should obey lexicographic ordering (two siblings version)
S4. Siblings should obey lexicographic ordering (more than two siblings version)
---------------------------------------------------------------------------------------------------------------*%
successor(X, Y) :- transition(X, _, Y).

% Left out; seems to be making it slower
% -successor(K, J) :- successor(I, J), not sibling(K, I), J > I, not goalState(J), state(K), 1 < K < I. % S1
% sibling(X, Y) :- successor(Z, X), successor(Z, Y), X != Y.

:- successor(I, J), not goalState(J), J > I, J > 1, {successor(K, J-1): state(K), state(J-1), K <= I} 0. % S2

:- maxND(N), N<3, precedence(E1, E2), transition(S, E1, J1), J1 > S, not goalState(J1), 1 {transition(S, E2, J2): J2<J1, J2>S, not goalState(J2)}. % S3
:- maxND(N), N>2, precedence(E1, E2), transition(S, E1, J1), transition(S, E2, J2), S < J2 < J1, not goalState(J1), {transition(S, E3, J2): precedence(E3, E2), not goalState(J2)} = 0. % S4


%*---------------------------------------------------------------------------------------------------------------
::: Mutex (derived from SAS encoding). In any state, there should be at most one mutually exclusive variable value pairs.
---------------------------------------------------------------------------------------------------------------*%
:- mutexGroup(Group), state(State), not {holds(State, Variable, Value) : mutex(Group, Variable, Value)} 1.

%*---------------------------------------------------------------------------------------------------------------
::: Strong cyclic solution: Goal should be reachable from all states. This is specified by three constraints.

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

