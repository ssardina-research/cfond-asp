%*---------------------------------------------------------------------------------------------------------------
ASP based encoding for computing a FOND controller, inspired by FondSat, fueled by Clingo.
---------------------------------------------------------------------------------------------------------------*%
#include "controller-common.lp".

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
:::STRONG SOLUTION: This is specified by three constraints.
---------------------------------------------------------------------------------------------------------------*%
terminates(X) :- goalState(X).
terminates(X) :- state(X), terminates(Y): successor(X, Y).
:- not terminates(X), state(X).

% NOTE: these are not equivalent to the 2nd rule above!
% they will support the derivation of terminates(X) when it shouldn't!
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