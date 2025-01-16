%*---------------------------------------------------------------------------------------------------------------
On table

goal(5, 0).
goal(6, 0).
goal(7, 3).
goal(8, 5).
goal(9, 4).
goal(10, 2).
goal(11, 7). -- on table
goal(12, 1).

subgoal(State, 1) :- holds(State, 11, 7).
subgoal(State, 7) :- holds(State, 5, 0).
subgoal(State, 5) :- holds(State, 7, 3).
subgoal(State, 2) :- holds(State, 8, 5).

subgoal(State, 4) :- holds(State, 9, 4).
subgoal(State, 3) :- holds(State, 10, 2).
subgoal(State, 6) :- holds(State, 12, 1).

holds(X, 5, 0):- goalState(X).
---------------------------------------------------------------------------------------------------------------*%
% ontable(State, "b1") :- holds(State, 7, 7).
% ontable(State, "b2") :- holds(State, 8, 7).
% ontable(State, "b3") :- holds(State, 9, 7).
% ontable(State, "b4") :- holds(State, 10, 7).
% ontable(State, "b5") :- holds(State, 11, 7).
% ontable(State, "b6") :- holds(State, 12, 7).

% clear(State, "b6") :- holds(State, 5, 0).
% emptyhand(State) :- holds(State, 6, 0).
% on(State, "b1", "b3") :- holds(State, 7, 3).
% on(State, "b2", "b5") :- holds(State, 8, 5).
% on(State, "b3", "b4") :- holds(State, 9, 4).
% on(State, "b4", "b2") :- holds(State, 10, 2).
% on(State, "b6", "b1") :- holds(State, 12, 1).

%% Unstack operation
% subgoal(State, 1) :- holds(State, 7, 7), holds(State, 8, 7), holds(State, 9, 7), holds(State, 10, 7), holds(State, 11, 7), holds(State, 12, 7), state(State).
#program check(t). % t=1,2,...
subgoal(State, 1) :- holds(State, 11, 7), State=t.
subgoal(State, 2) :- subgoal(State, 1), holds(State, 8, 5), State=t.
subgoal(State, 3) :- subgoal(State, 2), holds(State, 10, 2), State=t.
subgoal(State, 4) :- subgoal(State, 3), holds(State, 9, 4), State=t.
subgoal(State, 5) :- subgoal(State, 4), holds(State, 7, 3), State=t.
subgoal(State, 6) :- subgoal(State, 5), holds(State, 12, 1), State=t.
subgoal(State, 7) :- subgoal(State, 6), holds(State, 5, 0), State=t.

% :- subgoal(State1, G1), subgoal(State2, G2), G1<G2, State1>State2.
:- query(t), subgoal(State1, G1), G1>1, {subgoal(State2, G2): G2 < G1, State2 <= State1} 0.

#show subgoal/2.

