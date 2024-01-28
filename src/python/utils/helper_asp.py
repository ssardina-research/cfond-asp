import os
from typing import List
from base.config import *
from base.elements import Variable, State, Action
from itertools import combinations
import numpy as np

from utils.asp_output import parse_undo_actions


def write_variables(file, variables: List[Variable]):
    with open(file, "w+") as f:
        f.write(f"{ASP_VARIABLE_TERM}(0..{len(variables) - 1}).\n")
        for var_id in range(len(variables)):
            var = variables[var_id]
            f.write(f"{ASP_VARIABLE_ATOM_TERM}({var_id}, 0..{len(var.domain) - 1}).\n")
        f.write("\n")


def write_mutex(file, mutexs: List[State]):
    if len(mutexs) == 0:
        return

    variables: List[Variable] = mutexs[0].variables
    counter = 0
    with open(file, "a") as f:
        for idx in range(len(mutexs)):
            state: State = mutexs[idx]
            count = np.count_nonzero(np.array(state.values) != -1)
            if count > 1:
                counter += 1
                f.write(f"{ASP_MUTEX_GROUP_TERM}({counter}).\n")
                for var_id in range(len(state.variables)):
                    val = state.values[var_id]
                    if val != -1:
                        f.write(f"{ASP_MUTEX_TERM}({counter}, {var_id}, {val}).\n")

        for var_id in range(len(variables)):
            variable = variables[var_id]
            counter += 1
            f.write(f"{ASP_MUTEX_GROUP_TERM}({counter}).\n")
            for i in range(len(variable.domain)):
                f.write(f"{ASP_MUTEX_TERM}({counter}, {var_id}, {i}).\n")
        f.write("\n")


def write_initial_state(file, state: State, encoding="both"):
    if encoding == "pos":
        write_initial_state_positive(file, state)
    elif encoding == "neg":
        write_initial_state_negated(file, state)
    else:
        write_initial_state_positive(file, state)
        write_initial_state_negated(file, state)


def write_initial_state_positive(file, state: State):
    with open(file, "a") as f:
        for var_idx, var in enumerate(state.variables):
            val = state.values[var_idx]
            f.write(f"{ASP_HOLDS_TERM}(X, {var_idx}, {val}):- {ASP_INITIAL_STATE_TERM}(X).\n")

        f.write("\n")


def write_initial_state_negated(file, state: State):
    with open(file, "a") as f:
        for var_idx, var in enumerate(state.variables):
            val = state.values[var_idx]
            # f.write(f"{ASP_HOLDS_TERM}(X, {var_idx}, {val}):- {ASP_INITIAL_STATE_TERM}(X).\n")
            other_values = [i for i in range(len(var.domain)) if i != val]
            for other_val in other_values:
                f.write(f"-{ASP_HOLDS_TERM}(X, {var_idx}, {other_val}):- {ASP_INITIAL_STATE_TERM}(X).\n")

        f.write("\n")


def write_goal_state(file, state: State):
    with open(file, "a") as f:
        for var_idx, var in enumerate(state.variables):
            val = state.values[var_idx]
            if val != -1:
                f.write(f"{ASP_HOLDS_TERM}(X, {var_idx}, {val}):- {ASP_GOAL_STATE_TERM}(X).\n")
                f.write(f"{ASP_GOAL_TERM}({var_idx}, {val}).\n")

        f.write("\n")

def write_goal(file, state: State):
    with open(file, "a") as f:
        for var_idx, var in enumerate(state.variables):
            val = state.values[var_idx]
            if val != -1:
                f.write(f"{ASP_GOAL_TERM}({var_idx}, {val}).\n")

        f.write("\n")

def write_actions(file, nd_actions, variables, variable_mapping=False, precedence=True):
    total_variables = set(range(len(variables)))
    action_types = []
    max_nd_effect = 1
    with open(file, "a") as f:
        for action_name, det_actions in nd_actions.items():
            action_type = det_actions[0].prefix_name

            # write the action type
            if action_type not in action_types:
                action_types.append(action_type)
                f.write(f'{ASP_ACTION_TYPE_TERM}("{action_type}"). \n')

            # associate action type with action
            first_action: Action = det_actions[0]
            _name = get_ndet_action_string(first_action)

            f.write(f'{ASP_ACTION_TYPE_TERM}("{action_type}", "{_name}"). \n')
            f.write(f'{ASP_ACTION_TERM}("{_name}"). \n')

            # precondition
            prec: State = first_action.precondition
            for var_idx, var in enumerate(prec.variables):
                val = prec.values[var_idx]
                if val != -1:
                    f.write(f'{ASP_PREC_TERM}("{_name}", {var_idx}, {val}). \n')

            # effects
            num_effects = len(det_actions)
            f.write(f'{ASP_EFFECT_COUNT_TERM}("{_name}", {num_effects}). \n')

            if num_effects > max_nd_effect:
                max_nd_effect = num_effects

            for i in range(num_effects):
                affected_vars = set()
                action: Action = det_actions[i]

                # if num_effects == 1:
                #     effect = f"{ASP_EFFECT_TERM}0"
                # else:
                effect = f"{ASP_EFFECT_TERM}{i+1}"

                f.write(f'{ASP_ACTION_EFFECT_TERM}("{_name}", "{effect}"). \n')

                # add
                for var_idx in range(len(action.add)):
                    val = action.add[var_idx]
                    if val != -1:
                        affected_vars.add(var_idx)
                        f.write(f'{ASP_ADD_TERM}("{_name}", "{effect}", {var_idx}, {val}). \n')

                # del
                for var_idx in range(len(action.delete)):
                    vals = action.delete[var_idx]
                    if len(vals) > 0:
                        for val in vals:
                            affected_vars.add(var_idx)
                            f.write(f'{ASP_DEL_TERM}("{_name}", "{effect}", {var_idx}, {val}). \n')

                # affects
                if variable_mapping:
                    # for var_idx in affected_vars:
                    #     # f.write(f'{ASP_AFFECTS_TERM}("{_name}", "{effect}",  {var_idx}). \n')
                    unaffected_vars = total_variables.difference(affected_vars)
                    for var_idx in unaffected_vars:
                        f.write(f'not{ASP_AFFECTS_TERM}("{_name}","{effect}", {var_idx}). \n')

        if precedence and max_nd_effect > 1:
            for i in range(1, max_nd_effect):
                f.write(f'precedence("{ASP_EFFECT_TERM}{i}", "{ASP_EFFECT_TERM}{i+1}"). \n')

        f.write(f"{ASP_NDSIZE_TERM}({max_nd_effect}).\n")
        f.write("\n")


def write_siblings(file, nd_actions, precedence=True):
    num_effects = {}
    max_nd_effect = 1
    with open(file, "a") as f:
        for _nd_actions in nd_actions.values():
            nd_effect_size = len(_nd_actions)
            if max_nd_effect < nd_effect_size:
                max_nd_effect = nd_effect_size

            if len(_nd_actions) > 0:
                pairs = list(combinations(_nd_actions, 2))
                for (i, j) in pairs:
                    _name_1 = get_action_name(i)
                    _name_2 = get_action_name(j)
                    f.write(f"{ASP_SIBLING_TERM}({_name_1}, {_name_2}). \n")
                    f.write(f"{ASP_SIBLING_TERM}({_name_2}, {_name_1}). \n")

                    if precedence:
                        f.write(f"precedence({_name_1}, {_name_2}). \n")

            if _nd_actions[0].prefix_name not in num_effects:
                count = len(_nd_actions)
                num_effects[_nd_actions[0].prefix_name] = count
                f.write(f'{ASP_EFFECT_COUNT_TERM}("{_nd_actions[0].prefix_name}", {count}).\n')

        f.write(f"{ASP_NDSIZE_TERM}({max_nd_effect}).\n")
        f.write("\n")


def get_action_name(action: Action):
    asp_args: str = (','.join(action.arguments))
    if len(action.arguments) > 0:
        action_name = f'"{action.name}({asp_args})"'
    else:
        action_name = f'"{action.name}()"'

    return action_name


def get_det_action_string(action: Action):
    asp_args: str = (', '.join('"' + item + '"' for item in action.arguments))
    if len(action.arguments) > 0:
        det_action: str = f'action(("{action.name}", {asp_args}))'
    else:
        det_action: str = f'action("{action.name}")'
    return det_action


def get_ndet_action_string(action: Action):
    nd_action: str = f'{action.prefix_name}({",".join(action.arguments)})'
    return nd_action


def write_undo_actions(clingo_output_file: str, grounded_undo_file: str, process_action_type=False):
    undo_actions = parse_undo_actions(clingo_output_file)
    constraints = []
    undo_action_types = {}
    for [a1, a2] in undo_actions:
        if process_action_type and action_type(a1) != action_type(a2):
            if action_type(a1) not in undo_action_types:
                undo_action_types[action_type(a1)] = action_type(a2)
        else:
            line = f':- {{policy(S2, "{a2}"): policy(S1, "{a1}"), transition(S1,"e1", S2)}}!=0.\n'
            constraints.append(line)

    # :- {policy(S2, A2): policy(S1, A1), actionType("go-up", A2), actionType("go-down", A1), transition(S1,"e1", S2)}!=0.
    for a1_type, a2_type in undo_action_types.items():
        line = f':- {{policy(S2, A2): policy(S1, A1), actionType("{a1_type}", A2), actionType("{a2_type}", A1), transition(S1,"e1", S2)}}!=0.\n'
        constraints.append(line)

    with open(grounded_undo_file, "w+") as f:
        f.writelines(constraints)


def action_type(action: str):
    # assume first '(' is the divider before action name and arguments
    return action.split('(')[0].strip()