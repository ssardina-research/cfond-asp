
%*---------------------------------------------------------------------------------------------------------------
Backbone: Actions
---------------------------------------------------------------------------------------------------------------*%
:- {policy(State, Action): state(State), Action = "move-forward-door-open_DETDUP_0(l1,l2,d2,d3)"} 0.
:- {policy(State, Action): state(State), Action = "move-forward-last-door-open_DETDUP_0(l2,l3,d3)"} 0.

%*---------------------------------------------------------------------------------------------------------------
Backbone: Sequence
---------------------------------------------------------------------------------------------------------------*%
nextAction(A1, A2) :- transition(State, A1, NextState), policy(NextState, A2), state(State).

:- {nextAction(A1, A2): A1 = "move-forward-door-open_DETDUP_0(l1,l2,d2,d3)", A2 =  "move-forward-last-door-open_DETDUP_0(l2,l3,d3)"} 0.
#show nextAction/2.
