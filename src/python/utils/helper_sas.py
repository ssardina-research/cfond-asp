from typing import List
from base.config import DETERMINISTIC_ACTION_SUFFIX
from base.elements import Variable, Action, State
from utils.helper_str import get_indices_between
import re

re_action_name = rf"(?P<prefix>[a-zA-z-_\d]+){DETERMINISTIC_ACTION_SUFFIX}[\d]+"


def get_indices_initial_state(sas_info: List[str]) -> tuple[int, int]:
    """
    Returns the indices corresponding to the start and end of information encoding the initial state of the planning problem
    :param sas_info: Information from the SAS file
    :return: start and end indices of the information encoding the initial state.
    """
    return get_indices_between(sas_info, "begin_state", "end_state")[0]


def get_indices_mutex(sas_info: List[str]) -> List[tuple[int, int]]:
    """
    Returns the indices corresponding to the start and end of mutually exclusive values of variables
    :param sas_info: Information from the SAS file
    :return: start and end indices of the information encoding the mutex grouping
    """
    return get_indices_between(sas_info, "begin_mutex_group", "end_mutex_group")


def get_indices_goal(sas_info: List[str]) -> tuple[int, int]:
    """
    Returns the indices corresponding to the start and end of information encoding the goal state of the planning problem
    :param sas_info: Information from the SAS file
    :return: start and end indices of the information encoding the goal state.
    """
    return get_indices_between(sas_info, "begin_goal", "end_goal")[0]


def get_indices_operators(sas_info: List[str]) -> List[tuple[int, int]]:
    """
    Returns the list of index pairs corresponding to the start and end of information encoding each operator of the planning problem
    :param sas_info: Information from the SAS file
    :return: List of tuple pairs of indices where each pair denotes information of an operator.
    """
    return get_indices_between(sas_info, "begin_operator", "end_operator")


def get_indices_variables(sas_info: List[str]) -> List[tuple[int, int]]:
    """
    Returns the list of index pairs corresponding to the start and end of information encoding each variable of the planning problem
    :param sas_info: Information from the SAS file
    :return: List of tuple pairs of indices where each pair denotes information of a variable.
    """
    return get_indices_between(sas_info, "begin_variable", "end_variable")


def get_variable(var_info: List[str]) -> Variable:
    """
    A variable encoding in SAS includes begins with the name of the variable, followed by a number indicating if it has an axiom layer.
    Currently, we do not support axioms. The next line has a number indicating the size of the variable's domain. This is followed by the symbolic names of the values.
    The values start from index 0.

    Example:
        var0
        -1
        2
        Atom clear(b1)
        NegatedAtom clear(b1)
    :param var_info: variable information from the SAS file
    :return: variable object encoding the given information
    """
    var_info = [l.strip() for l in var_info]

    var_name: str = var_info[0]
    num_values: int = int(var_info[2])
    values: List[str] = []
    for i in range(3, 3 + num_values):
        values.append(var_info[i])

    variable = Variable(name=var_name, domain=values)
    return variable


def get_action(op_info: List[str], variables: List[Variable]) -> Action:
    """
    The actions are read from the all outcomes determinization by the SAS translator.
    Actions with "oneof" in effects have their names suffixed with "_DET_n" where n is the index of the oneof effect and DET is the suffix (this can be changed in the config).
    Note that there may be a deterministic action with a single oneof in its effect. Such an action will have "DETDUP_0" suffix in its name.
    Names of deterministic actions (i.e., those without "oneof") are left as is.
    Finally, SAS produces grounded actions where the arguments of the action are added to the action name.

    Example of determinisation of a non-deterministic action:
        pick-up_DET_1 b2 b4
            2
            1 0
            5 0
            2
            0 3 -1 0
            0 7 4 6
            0

    Example of a deterministic action:
        put-down b1
            0
            3
            0 0 -1 0
            0 5 -1 0
            0 6 0 6
            0

    :param op_info: Action information from the SAS file
    :param variables: list of variables in the domain
    :return: An action object encoding the given information

    Note: The SAS encoding has a so-called "precondition" on the variable's previous value.
    For example the last effect in deterministic action "put-down b1" requires variable 6 to have a previous value of 0.
    In the action's encoding we lift this variable's precondition to the action's precondition. Also see `:py:class:base.elements.Action`.
    """
    op_info = [l.strip() for l in op_info]

    full_action_name: str = op_info[0]
    action_name, prefix_name, op_args = _get_action_info(full_action_name)
    cost: int = int(op_info[-1])

    num_preconditions: int = int(op_info[1])
    num_effects_vars: int = int(op_info[2 + num_preconditions])
    precondition: State = State(variables, [-1] * len(variables))
    effect: State = State(variables, [-1] * len(variables))

    # preconditions
    start = 2
    for i in range(start, start + num_preconditions):
        [var_idx, val_idx] = map(int, op_info[i].split())
        precondition.values[var_idx] = val_idx

    # effect
    start = 3 + num_preconditions
    for i in range(start, start + num_effects_vars):
        [num_conf_eff, var_idx, prev_val, next_val] = map(int, op_info[i].split())
        if prev_val != -1:  # lift the precondition of the variable to the precondition of the action
            precondition.values[var_idx] = prev_val
        effect.values[var_idx] = next_val

    action = Action(name=action_name, prefix_name=prefix_name, arguments=op_args, precondition=precondition, effects=[effect], cost=cost)

    return action


def _get_action_info(full_action_name):
    """
    Returns the actions name, prefix (same as the domain pddl file), and arguments.

    Example: The full action name "pick-up_DET_1 b2 b4" has "pick-up_DET_1" as action name, "pick-up" as prefix and ["b1", "b2", "b4"] as arguments.
    Example: The full action name "put-down b1" has name and prefix as "put-down" and ["b1"] as arguments
    :param full_action_name:
    :return: action name, prefix name, and arguments

    Note: The suffix "_DET_" can be changed in the configuration.
    """
    if DETERMINISTIC_ACTION_SUFFIX.lower() in full_action_name.lower():  # action has an "oneof" in its effect
        action_name = full_action_name.split()[0]
        prefix_name = re.match(re_action_name, action_name, re.IGNORECASE).group("prefix")
        assert prefix_name in action_name  # this is as a temp check
        op_args: List[str] = full_action_name.lower().split(DETERMINISTIC_ACTION_SUFFIX.lower())[1].split(" ")[1:]
    else:  # action is deterministic
        action_name = full_action_name.split()[0]
        prefix_name = action_name
        op_args: List[str] = full_action_name.split()[1:]
    return action_name, prefix_name, op_args,


def organize_actions(actions: List[Action]) -> (dict[str: Action], dict[str: List[Action]]):
    """
    Organises the actions based on their actual name and arguments.
    Since the all outcomes determinization creates duplicate actions, each with one effect, one needs a way to match the duplicated action with its non-deterministic counterpart.
    We do this matching based on the action names (since the determinization adds "_DET_{n}", n >=0, suffix to an action's name)
    :param actions: List of actions
    :return: Two dictionaries, the first dictionary maps a deterministic action and arguments to its action object.
    The second dictionary maps a deterministic action and arguments to list of actions that may ensue due to the original action being non-deterministic.

    Note: We do not create a new action to encode non-deterministic effects. Instead, a non-deterministic action is denoted by a list of its determinised actions.
    This is done for space efficiency.
    """

    actions_dict = {}
    nondet_actions_dict = {}
    for a in actions:
        name, prefix, op_args = a.name, a.prefix_name, a.arguments
        nondet_key = get_action_key(prefix, op_args)  # for example 'pick-up(b1,b2)'
        det_key = get_action_key(name, op_args)  # for example 'pick-up_det_1(b1,b2)'

        if nondet_key not in nondet_actions_dict:
            nondet_actions_dict[nondet_key] = []

        nondet_actions_dict[nondet_key].append(a)  # the value is list of all determinised actions of this possibly non-deterministic action
        actions_dict[det_key] = a

    return actions_dict, nondet_actions_dict


def get_action_key(name: str, op_args: List[str]):
    """
    A helper method to create key to be used in a dictionary that stores actions.
    :param name: Name of the action
    :param op_args: Action arguments
    :return: A key combining name and arguments

    For deterministic actions the action name should be used, for non-deterministic actions the action prefix should be used.
    """
    det_key = f"{name}({','.join(op_args)})"
    return det_key
