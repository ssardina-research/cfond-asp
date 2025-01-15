import os
import re
from cfondasp.base.config import (
    DETERMINISTIC_ACTION_SUFFIX,
    ASP_OUT_LINE_END,
    ASP_OUT_DIVIDER,
)

re_holds = r"holds\((?P<state>[\d]+),(?P<variable>[\d]+),(?P<value>[\d]+)\)"
re_transition = r"transition\((?P<from>[\d]+),\"(?P<action>[\a-z-\(\d\,\)]+)\",(?P<to>[\d]+)\)"
re_policy = r"policy\((?P<from>[\d]+),\"(?P<action>[\a-z-\(\d\,\)]+)\"\)"
re_action = rf"(?P<action>[a-z-\d]+){DETERMINISTIC_ACTION_SUFFIX}[\d]+(?P<arguments>\([a-z-\d,]+\))"


def parse_undo_actions(clingo_output_file: str):
    with open(clingo_output_file) as f:
        data = f.readlines()

    for _i in range(len(data)):
        line = data[_i]
        if "answer" in line.lower():
            output = data[_i + 1]

    undo_actions_terms = output.split()
    undo_actions = [[a.replace('"', '') for a in t[len("undo("): -1].split('","')] for t in undo_actions_terms]
    return undo_actions


def parse_clingo_output(log_file: str, out_file: str):
    """Parse a Clingo output answer model and produce corresponding controller solution file"""
    if os.path.exists(out_file):
        os.remove(out_file)
    atoms_dict = get_atoms(log_file)
    for answer, atoms in atoms_dict.items():
        transitions = {}
        state_variables = {}
        policy = {}

        for atom in atoms:
            atom = atom.replace(" ", "").strip()
            if "holds" in atom:
                state, value, variable = get_state_info(atom)
                if state not in state_variables:
                    state_variables[state] = []

                state_variables[state].append((variable, value))

            elif "policy" in atom:
                action, from_state = get_policy_info(atom)
                policy[from_state] = action

            elif "transition" in atom:
                action, next_state, state = get_transition_info(atom)

                # Important! next state could be a dead end state. If this is the case it may not be in holds()
                if next_state not in state_variables:
                    state_variables[next_state] = []

                if state not in transitions:
                    transitions[state] = []
                transitions[state].append((state, action, next_state))

        write_output(answer, state_variables, transitions, policy, out_file)

        return state_variables  # state variables are used later to store the controller


def get_parent_name(action):
    if DETERMINISTIC_ACTION_SUFFIX.lower() in action.lower():
        result = re.match(re_action, action)
        action = result.group("action")
        arguments = result.group("arguments")
        parent_action = f"{action}{arguments}"

    else:
        parent_action = action

    return parent_action


def write_output(answer, state_variables, transitions, policy, out_file: str):
    with open(out_file, "a+") as f:
        f.write(f"ANSWER:{answer}\n")
        f.write(f"{ASP_OUT_DIVIDER}\n")

        f.write(f"Initial State:0\n")
        f.write(f"{ASP_OUT_DIVIDER}\n")

        f.write(f"Goal State:{len(state_variables)-1}\n")
        f.write(f"{ASP_OUT_DIVIDER}\n")

        # f.write(f"{ASP_OUT_LINE_END}\n")
        for state in sorted(state_variables.keys()):
            f.write(f"State:{state}\n")
            for key in sorted(state_variables[state]):
                variable, value = key
                line = f"{variable}={value}\n"
                f.write(line)

        f.write(f"{ASP_OUT_DIVIDER}\n")

        # sort them for better readability
        states = sorted(transitions.keys())
        f.write(f"Transitions:\n")
        for state in states:
            txs = transitions[state]
            for t in txs:
                state, effect, next_state = t
                action = policy[state]
                line = f"{state}--{action},{effect}-->{next_state}\n"
                f.write(f"{line}")

        f.write(f"{ASP_OUT_DIVIDER}\n")

        f.write(f"Policy:\n")
        for state in states:
            action = policy[state]
            line = f"{state}-->{action}\n"
            f.write(line)

        f.write(f"{ASP_OUT_DIVIDER}\n")


def get_transition_info(atom):
    result = re.match(re_transition, atom)
    state = int(result.group("from"))
    action = result.group("action")
    next_state = int(result.group("to"))
    return action, next_state, state


def get_policy_info(atom):
    result = re.match(re_policy, atom)
    state = int(result.group("from"))
    action = result.group("action")
    return action, state


def get_state_info(atom):
    result = re.match(re_holds, atom)
    variable = int(result.group("variable"))
    value = int(result.group("value"))
    state = int(result.group("state"))
    return state, value, variable


def get_atoms(log_file):
    atoms = {}
    data = []
    with open(log_file) as f:
        data = f.readlines()
    for i in range(3, len(data)):
        d = data[i]
        if "answer" in d.lower():
            ans = int(d.split(":")[1])
            atoms_info = data[i+1]
            atoms[ans] = atoms_info.split(" ")

    return atoms


if __name__ == "__main__":
    out_file = "./output/controller.out"
    parse_clingo_output("./output/solution.out", out_file)
