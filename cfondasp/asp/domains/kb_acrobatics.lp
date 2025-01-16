% Knowledge
undoPolicy("walk-right", "walk-left").
undoPolicy("walk-left", "walk-right").


deadendGroup(0).
deadend(0, 0, 0).

minPolicy("walk-left", 15).
% maxPolicy("walk-left", 7).

minPolicy("walk-on-beam", 15).
% maxPolicy("walk-on-beam", 7).

% Rules
:- successor(State, NextState), metaPolicy(State, A1), metaPolicy(NextState, A2), undoPolicy(A1, A2).
:- deadendGroup(G), holds(State, Variable, Value), deadend(G, Variable, Value).
% :-  not Z {metaPolicy(State, ActionType): state(State)}, minPolicy(ActionType, Z).
% :-  not {metaPolicy(State, ActionType): state(State)} Z, maxPolicy(ActionType, Z).
% :-  not Z {metaPolicy(State, ActionType): state(State)} Z, minPolicy(ActionType, Z).