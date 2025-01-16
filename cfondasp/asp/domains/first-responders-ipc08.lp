% :- {policy(S2, A2): policy(S1, A1), actionType("walk-left", A2), actionType("walk-right", A1), transition(S1,"e1", S2)}!=0.
% :- {policy(S2, A2): policy(S1, A1), actionType("walk-right", A2), actionType("walk-left", A1), transition(S1,"e1", S2)}!=0.

% :- {policy(S2, "load-medical-unit(m1,l1,v3)"): policy(S1, "unload-medical-unit(m1,l1,v3)"), transition(S1,"e1", S2)}!=0.
% :- {policy(S2, "unload-medical-unit(m1,l1,v1)"): policy(S1, "load-medical-unit(m1,l1,v1)"), transition(S1,"e1", S2)}!=0.

:- {policy(S2, A2): policy(S1, A1), actionType("load-medical-unit(", A2), actionType("unload-medical-unit", A1), transition(S1,"e1", S2)}!=0.
:- {policy(S2, A2): policy(S1, A1), actionType("unload-medical-unit", A2), actionType("load-medical-unit(", A1), transition(S1,"e1", S2)}!=0.
