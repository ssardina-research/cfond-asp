%*---------------------------------------------------------------------------------------------------------------
ASP based encoding for computing a FOND controller, inspired by REGRESSION/PRP, fueled by Clingo.
---------------------------------------------------------------------------------------------------------------*%
#include "controller-common.lp".

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
:::STRONG CYCLIC SOLUTION: Goal should be reachable from all states. This is specified by three constraints.

S1. Goal is reachable from the goal state.
S2. If goal is reachable from a state Y, then goal is reachable from all states X, such that Y is a successor of X.
S3. It should not beq the case that there is a state from where goal is unreachable.
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

