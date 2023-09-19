% :- {policy(S2, A2): policy(S1, A1), actionType("walk-left", A2), actionType("walk-right", A1), transition(S1,"e1", S2)}!=0.
% :- {policy(S2, A2): policy(S1, A1), actionType("walk-right", A2), actionType("walk-left", A1), transition(S1,"e1", S2)}!=0.

% :- {policy(S2, "climb-bridge(m2,l11-2)"): policy(S1, "leave-bridge(m2,l11-2)"), transition(S1,"e1", S2)}!=0.
% :- {policy(S2, "leave-bridge(m1,l11-1)"): policy(S1, "climb-bridge(m1,l11-1)"), transition(S1,"e1", S2)}!=0.

:- {policy(S2, A2): policy(S1, A1), actionType("climb-bridge", A2), actionType("leave-bridge", A1), transition(S1,"e1", S2)}!=0.
:- {policy(S2, A2): policy(S1, A1), actionType("leave-bridge", A2), actionType("climb-bridge", A1), transition(S1,"e1", S2)}!=0.
