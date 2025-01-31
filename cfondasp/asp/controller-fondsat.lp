%*---------------------------------------------------------------------------------------------------------------
ASP based encoding for computing a FOND controller, inspired by FONDSAT, fueled by Clingo.
---------------------------------------------------------------------------------------------------------------*%
#include "controller-common.lp".

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

