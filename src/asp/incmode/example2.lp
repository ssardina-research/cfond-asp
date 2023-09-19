#const istop  = "SAT".
#const imin   = 1.
#const imax   = 6.

{a;b;c}.
#program base.


#program step(k).
state(k).
0{t(State, k): state(State)}1.
0{t(k, State): state(State)}1.

q(k,k) :- t(k, _).
q(A,k) :- t(A, k).

#program check(k).
:- not q(3,_), query(k).
% :- not c(2).