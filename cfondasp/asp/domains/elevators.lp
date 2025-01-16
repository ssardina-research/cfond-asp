% :- {policy(S2, A2): policy(S1, A1), actionType("walk-left", A2), actionType("walk-right", A1), transition(S1,"e1", S2)}!=0.
% :- {policy(S2, A2): policy(S1, A1), actionType("walk-right", A2), actionType("walk-left", A1), transition(S1,"e1", S2)}!=0.

% :- {policy(S2, "go-down(e1,f2,f1)"): policy(S1, "go-up(e1,f1,f2)"), transition(S1,"e1", S2)}!=0.
% :- {policy(S2, "go-up(e2,f1,f2)"): policy(S1, "go-down(e2,f2,f1)"), transition(S1,"e1", S2)}!=0.
% :- {policy(S2, "move-left-nogate(f1,p2,p1)"): policy(S1, "move-right-nogate(f1,p1,p2)"), transition(S1,"e1", S2)}!=0.
% :- {policy(S2, "move-right-nogate(f1,p1,p2)"): policy(S1, "move-left-nogate(f1,p2,p1)"), transition(S1,"e1", S2)}!=0.
% :- {policy(S2, "step-in(e1,f1,p2)"): policy(S1, "step-out(e1,f1,p2)"), transition(S1,"e1", S2)}!=0.
% :- {policy(S2, "step-out(e1,f1,p2)"): policy(S1, "step-in(e1,f1,p2)"), transition(S1,"e1", S2)}!=0.

:- {policy(S2, A2): policy(S1, A1), actionType("go-down", A2), actionType("go-up", A1), transition(S1,"e1", S2)}!=0.
:- {policy(S2, A2): policy(S1, A1), actionType("go-up", A2), actionType("go-down", A1), transition(S1,"e1", S2)}!=0.

:- {policy(S2, A2): policy(S1, A1), actionType("move-left-nogate", A2), actionType("move-right-nogate", A1), transition(S1,"e1", S2)}!=0.
:- {policy(S2, A2): policy(S1, A1), actionType("move-right-nogate", A2), actionType("move-left-nogate", A1), transition(S1,"e1", S2)}!=0.

:- {policy(S2, A2): policy(S1, A1), actionType("step-in", A2), actionType("step-out", A1), transition(S1,"e1", S2)}!=0.
:- {policy(S2, A2): policy(S1, A1), actionType("step-out", A2), actionType("step-in", A1), transition(S1,"e1", S2)}!=0.