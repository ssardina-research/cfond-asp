% Knowledge
undoPolicy("pick-rock", "drop-rock").
undoPolicy("drop-rock", "pick-rock").

% person is not alive
deadendGroup(0).
deadend(0, 20, 1).


% Rules
:- successor(State, NextState), metaPolicy(State, A1), metaPolicy(NextState, A2), undoPolicy(A1, A2).
:- deadendGroup(G), holds(State, Variable, Value), deadend(G, Variable, Value).

#minimize {Z, p(S,A): metaPolicy(S, A), numEffects(A, Z)}.
