#const istop  = "SAT".
#const imin   = 1.
#const imax   = 5.

#program base.
state("goal").
goalState("goal").
initialState(1).
reachableG("goal", 0).% S1

#program step(k).
state(k).
0 {successor(k, NextState): state(NextState)} 1.
0 {successor(State, k): state(State), State < k, not goalState(State)} 1.


:- successor(I, J), J=k, I<k, not goalState(I), J>1, {successor(K, J-1):state(K), state(J-1), K <= I} 0. % S2

#program check(k).
{state(K): state(K)}>3 :- query(k).
reachableG(State, k) :- successor(State, NextState), reachableG(NextState, _),  query(k).  % S2
:- not reachableG(State, _), state(State),  query(k).  % S3

#show successor/2.
% #show reachableG/2.