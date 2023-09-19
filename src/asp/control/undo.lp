%*---------------------------------------------------------------------------------------------------------------
Extract Undo actions from instance!

Actions A1 and A2 undo each others effect if:
1. A1 and A2 are deterministic (i.e., number of effects is 1.)
2. add effect of A1 is del effect of A2
3. delete effect of A1 is add effect of A2
---------------------------------------------------------------------------------------------------------------*%

deterministic(Action) :- action(Action), numEffects(Action, 1).

disagree(Action1, Action2):- add(Action1, "e1", Variable1, _), deterministic(Action1), deterministic(Action2), not del(Action2, "e1", Variable1, _).
disagree(Action1, Action2):- del(Action1, "e1", Variable1, _), deterministic(Action1), deterministic(Action2), not add(Action2, "e1", Variable1, _).

disagree(Action1, Action2):- add(Action1, "e1", Variable, Value1), deterministic(Action2), {del(Action2, "e1", Variable, Value2): Value1 != Value2}!=0.
disagree(Action1, Action2):- del(Action1, "e1", Variable, Value1), deterministic(Action2), {add(Action2, "e1", Variable, Value2): Value1 != Value2}!=0.

undo(Action1, Action2) :- deterministic(Action1), deterministic(Action2), not disagree(Action1, Action2), not disagree(Action2, Action1).

% :- 1{ policy(S2, Action2): undo(Action1, Action2), policy(S1, Action1), transition(S1,"e1", S2), state(S1), state(S2)}. 

% #show deterministic/1.
#show undo/2.

