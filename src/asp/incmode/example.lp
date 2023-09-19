#const istop  = "SAT".
#const imin   = 1.
#const imax   = 6.
{a;b;c}.

#program base.


#program step(k).

{ c(k) }.
q(k) :- c(k).

#program check(k).
:- not c(2), query(k).
% :- not c(2).