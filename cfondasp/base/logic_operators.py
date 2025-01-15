from copy import copy
from cfondasp.base.elements import State
from cfondasp.base.elements import Action


def entails(state_1: State, state_2: State) -> bool:
    """
    Checks if state_1 entails state_2 (i.e., state_1 |= state_2)
    :param state_1: state 1
    :param state_2: state 2
    :return: True if state_1 entails state_2, False otherwise.

    state_1 entails state_2 if and only if: ∀v ∈ vars(state_2), state_1(v) = state_2(v),
    where vars(s) denotes the variables that are defined in state s (i.e., they are not -1).
    """

    # get the indices of variables that are defined in state_2
    defined_vars_idxs = [i for i, v in enumerate(state_2.values) if v >= 0]

    # check if state_1 agrees with state_2 on all these variables
    _entails = True
    for i in defined_vars_idxs:
        if state_1.values[i] != state_2.values[i]:
            _entails = False
            return _entails

    return _entails


def consistent(state_1: State, state_2: State) -> bool:
    """
    Checks if two states are consistent (i.e., state_1 ≈ state_2)
    :param state_1: state 1
    :param state_2: state 2
    :return: True if state_1 and state_2 are consistent, False otherwise.

    state_1 is consistent with state_2 (and vice versa) if ∀v∈V, state_1(v) = state_2(v) OR state_1(v) = -1 OR state_2(v) = -1.
    """
    _consistent = True
    for i, v in enumerate(state_1.values):
        if not (v == state_2.values[i] or v == -1 or state_2.values[i] == -1):
            _consistent = False
            return _consistent

    return _consistent


def update(state_1: State, state_2: State) -> State:
    """
    Returns the updated state obtained by applying state_2 to state_1 (i.e., state_1 ⊕ state_2)
    :param state_1: state 1
    :param state_2: state 2
    :return: state obtained by applying state_2 to state_1.

    The updated state obtained by applying state state_2 to state state_1 is the state state_3, where
    if v is defined in state_2 (i.e., v is not -1) then state_3(v) = state_2(v), else state_3(v) = state_1(v).
    """
    state_3 = copy(state_1)

    # get the indices of variables that are defined in state_2
    defined_vars_idxs = [i for i, v in enumerate(state_2.values) if v >= 0]
    for i in defined_vars_idxs:
        state_3.values[i] = state_2.values[i]

    return state_3


def progress(state: State, action: Action, effect_idx: int) -> State | None:
    """
    Returns the state progressed by applying the given effect of the action in the given state
    :param state: state
    :param action: action
    :param effect_idx: index of the effect in action
    :return: Progressed state obtained by applying the given effect of the action on the given state.

    The progression of a state state_1, with respect to an action A and selected (non-deterministic) effect with index i is a state state_2, where
    state_2 = state_1 ⊕ A.precondition ⊕ A.effects[i] if state_1 ≈ A.precondition, state_2 is None (i.e., undefined) otherwise.
    """

    if consistent(state, action.precondition):
        effect = action.effects[effect_idx]
        return update(update(state, action.precondition), effect)
    else:
        return None


def regress(state: State, action: Action, effect_idx: int) -> State | None:
    """
    Returns the partial state obtained by regressing the ith effect of given action on the given state
    :param state: state
    :param action: action
    :param effect_idx: index of the effect in action
    :return: state obtained by regressing the effect on the given state

    A partial state state_1 can be regressed via effect i of action A if and only if A.effects[i] ≈ state_1.
    The effect of regressing is a partial state state_2 such that for a variable v,
    - 1. state_2(v) = A.precondition(v) of v is defined in A.precondition
    - 2. state_2(v) = -1 if v is undefined in A.precondition and state_1(v) = A.effects(v)
    - 3. state_2(v) = state_1(v) otherwise
    """

    if consistent(state, action.effects[effect_idx]):
        state_2 = copy(state)

        # 1. state_2(v) = A.precondition(v) of v is defined in A.precondition
        defined_vars_idxs = [i for i, v in enumerate(action.precondition.values) if v >= 0]
        for i in defined_vars_idxs:
            state_2.values[i] = action.precondition.values[i]

        # 2. state_2(v) = -1 if v is undefined in A.precondition and state_1(v) = A.effects(v)
        undefined_vars_idxs = [i for i, v in enumerate(action.precondition.values) if v < 0]
        for i in undefined_vars_idxs:
            if action.effects[effect_idx].values[i] == state.values[i]:
                state_2.values[i] = -1

        return state_2
    else:
        return None
