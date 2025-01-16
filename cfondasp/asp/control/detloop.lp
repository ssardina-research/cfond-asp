deterministic(Action) :- action(Action), {actionEffect(Action, Effect): action(Action)} = 1.
:- transition(State, Action, State), deterministic(Action), state(State).