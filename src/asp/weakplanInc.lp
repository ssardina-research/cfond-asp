#const istop  = "SAT".
#const imin   = 0.
#const imax   = 100.

#include <incmode>.

#program base.
% Establish initial state
initialState(0).
policy(-1,-1,-1). % this is to avoid the initial error (no atoms over signature occur in program:  policy/3)

#program step(t). % t=1,2,...

% Perform actions
1 {policy(t, Action, Effect) : actionEffect(Action, Effect)} 1.

0 {holds(t,Variable,Value) : variableValue(Variable,Value)} 1 :- variable(Variable).

% Check preconditions
:- policy(t, Action, Effect), precondition(Action, Variable, Value), not holds(t-1, Variable, Value).

% Apply effects
not holds(t, Variable, Value) :- policy(t, Action, Effect), del(Action, Effect, Variable, Value). % N1
not holds(t, Variable, Value) :- not holds(t-1, Variable, Value), variableValue(Variable, Value), {policy(t, Action, Effect): add(Action, Effect, Variable, Value)} 0. % N2

% Check mutexes
:- mutexGroup(Group), not {holds(t, Variable, Value) : mutex(Group, Variable, Value)} 1.


#program check(t). % t=0,1,...
t > 3 :- query(t).

% Verify that goal is met
:- query(t), goal(Variable, Value), not holds(t, Variable, Value).

#show policy/3.
% #show holds/3.
