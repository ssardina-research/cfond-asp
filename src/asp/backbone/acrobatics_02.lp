% Solution
% (move-forward-door-open_DETDUP_0 l1 l2 d2 d3)
% (move-forward-door-open_DETDUP_0 l2 l3 d3 d4)
% (move-forward-last-door-open_DETDUP_0 l3 l4 d4)

%*---------------------------------------------------------------------------------------------------------------
Backbone: Actions
---------------------------------------------------------------------------------------------------------------*%
:- {policy(State, Action): state(State), Action = "move-forward-door-open_DETDUP_0(l1,l2,d2,d3)"} 0.
:- {policy(State, Action): state(State), Action = "move-forward-door-open_DETDUP_0(l2,l3,d3,d4)"} 0.
:- {policy(State, Action): state(State), Action = "move-forward-last-door-open_DETDUP_0(l3,l4,d4)"} 0.

%*---------------------------------------------------------------------------------------------------------------
Backbone: Sequence
---------------------------------------------------------------------------------------------------------------*%
backbone(A1,A2,A3) :- transition(0,A1,S2),transition(S2,A2,S3),state(S2),state(S1),policy(S3, A3), A1 = "move-forward-door-open_DETDUP_0(l1,l2,d2,d3)",A2 = "move-forward-door-open_DETDUP_0(l2,l3,d3,d4)",A3 = "move-forward-last-door-open_DETDUP_0(l3,l4,d4)".
:- {backbone(A1,A2,A3)} 0.

