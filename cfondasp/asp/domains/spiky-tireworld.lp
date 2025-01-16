% :- {policy(S2, A2): policy(S1, A1), actionType("walk-left", A2), actionType("walk-right", A1), transition(S1,"e1", S2)}!=0.
% :- {policy(S2, A2): policy(S1, A1), actionType("walk-right", A2), actionType("walk-left", A1), transition(S1,"e1", S2)}!=0.

% :- {policy(S2, "loadtire(ng,t1)"): policy(S1, "droptire(ng,t1)"), transition(S1,"e1", S2)}!=0.
% ::- {policy(S2, "droptire(nb4,t2)"): policy(S1, "loadtire(nb4,t2)"), transition(S1,"e1", S2)}!=0.

:- {policy(S2, A2): policy(S1, A1), actionType("loadtire", A2), actionType("droptire", A1), transition(S1,"e1", S2)}!=0.
:- {policy(S2, A2): policy(S1, A1), actionType("droptire", A2), actionType("loadtire", A1), transition(S1,"e1", S2)}!=0.
