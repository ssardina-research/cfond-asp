"""
The script estimates different metrics for estimating controller size (e.g., using shortest weak plan).
"""
import argparse
import logging
import os.path
import re
import subprocess
from dataclasses import dataclass
from typing import List
import coloredlogs
from copy import deepcopy
from base.elements import Variable, Action
from utils.helper_sas import organize_actions
from utils.translators import parse_sas

SEARCH_HEURISTIC = "astar(lmcut())"
re_plan_length = r"(?P<length>[\d]+) step\(s\)\."
re_time = r"(?P<time>[.\d]+)s"
MAIN_FILE = "src/python/main.py"  # relative to cwd
FD_PATH = os.path.expanduser("~/Tools/Planners/fd/fast-downward.py")
FD_ROOT = os.path.expanduser("~/Tools/Planners/fd/")
OUTPUT_FOLDER = "./output"
OUTPUT_FILE = "./output/weak_plan.csv"
SRC_ROOT = os.path.expanduser("~/Work/Software/fond-compact-asp/")


@dataclass(slots=True, frozen=True)
class ControllerState(object):
    """
    A state of the controller. A state consists of variables along with their assigned values.
    A controller state can define values that hold and values that do not hold in a state.

    Give a variable v, its values are denoted by a list. For example, if a variable v can hold three values [a, b, c],
    a state value of [-1, 1, 0] implies that v=a cannot hold in the state, v=b holds, and v=c is unknown.
    """
    variables: List[Variable]
    values: List[List[int]]

    def __eq__(self, state) -> bool:
        return self.values == state.values

    def __copy__(self):
        state = ControllerState(variables=self.variables, values=self.values[:])
        return state

    def __hash__(self):
        tuples = [tuple(v) for v in self.values]
        return hash(tuple(tuples))


def get_args():
    args_parser = argparse.ArgumentParser(description='Batch determiniser')
    args_parser.add_argument('path', help='Path to the root folder containing configs.')

    return vars(args_parser.parse_args())


def _get_logger():
    logger = logging.getLogger("FDExecutor")
    coloredlogs.install(level='DEBUG')
    return logger


_logger = _get_logger()


def get_plan_size(output):
    """
    Extract the plan length from fast downward output
    :param output:
    :return:
    """
    plan_length = 0
    time = 0
    lines = output.split(os.linesep)
    for line in lines:
        if "Plan length" in line:
            tokens = line.split(":")
            result = re.match(re_plan_length, tokens[1].strip())
            plan_length = int(result.group("length"))
        elif "Total time" in line:
            tokens = line.split(":")
            result = re.match(re_time, tokens[1].strip())
            time = float(result.group("time"))

    return plan_length, time


def compute_weak_plan(input_files: List[str], plan_output: str, fd_path: str, cwd: str):
    """
    Run the fast downward planner on the determinised domain and instance, and extract the plan length from its output.
    :param input_files: input files to fd
    :param plan_output: file to save the computed plan
    :param fd_path: path to fast downward
    :param cwd: directory where fd should run
    :return: length of weak plan
    """
    plan_size = 0
    time = 0
    executable_list = [fd_path] + input_files + ['--evaluator', "hff=ff()", '--evaluator', "hcea=cea()"] + ['--search', "lazy_greedy([hff, hcea], preferred=[hff, hcea])"] # + ["--plan-file", plan_output]
    try:
        process = subprocess.Popen(executable_list, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        stdout, stderr = process.communicate()

        plan_size, time = get_plan_size(stdout.decode())
    except Exception as e:
        _logger.error(e)

    return plan_size, time


def determinise_scenario(folder: str):
    """
    Determinise all the problems by reading config files from the given folder.
    :param folder:
    :return:
    """
    _logger.info(f"Determinising instances from {folder} folder.")
    files = os.listdir(folder)
    config_files = sorted([f for f in files if f.endswith("ini")])
    for c in config_files:
        exec_str = f"python {MAIN_FILE} {folder}/{c} determinise"
        subprocess.call(exec_str, shell=True)


def run_fd(folder: str, output_file: str):
    data = [f"scenario,instance,weak_plan,fd_time\n"]

    scenarios = [s for s in os.listdir(folder) if os.path.isdir(f"{folder}/{s}")]
    for scenario in scenarios:
        _logger.info(f"Computing weak plans for {scenario} scenario.")
        scenario_path = f"{folder}/{scenario}"
        instances = os.listdir(scenario_path)
        for instance in instances:
            instance_path = f"{scenario_path}/{instance}"
            solvers = os.listdir(instance_path)
            for s in solvers:
                if "asp" in s:
                    _logger.info(f"---Computing weak plans for instance {instance}.")
                    fd_input = [f"{SRC_ROOT}/{instance_path}/{s}/output.sas"]
                    plan_output = f"{SRC_ROOT}/{instance_path}/{s}/plan.sas"
                    cwd = f"{SRC_ROOT}/{instance_path}/{s}"
                    plan_length, time = compute_weak_plan(fd_input, plan_output, FD_PATH, cwd)
                    data.append(f"{scenario},{instance},{plan_length},{time}\n")
                    continue

    with open(output_file, "w") as f:
        f.writelines(data)


def determinise(folder: str):
    scenarios = os.listdir(folder)
    for scenario in scenarios:
        scenario_path = f"{folder}/{scenario}"
        config_folders = os.listdir(scenario_path)
        for c in config_folders:
            if "asp" in c:
                determinise_scenario(f"{scenario_path}/{c}")
                continue


def run(folder: str):
    # determinise(folder)
    run_fd(OUTPUT_FOLDER, OUTPUT_FILE)


def get_initial_state(state):
    variables = state.variables
    values: List[List[int]] = [[]] * len(state.variables)
    for var_idx, var in enumerate(state.variables):
        val = state.values[var_idx]
        var_values = [0] * len(var.domain)
        other_values = [i for i in range(len(var.domain)) if i != val]
        for other_val in other_values:
            var_values[other_val] = -1
        values[var_idx] = var_values

    init_state: ControllerState = ControllerState(variables, values)
    return init_state


def get_goal_state(state):
    variables = state.variables
    values: List[List[int]] = [[]] * len(state.variables)
    for var_idx, var in enumerate(state.variables):
        val = state.values[var_idx]
        var_values = [0] * len(var.domain)
        if val != -1:
            var_values[val] = 1
        values[var_idx] = var_values

    goal_state: ControllerState = ControllerState(variables, values)
    return goal_state


def get_actions(plan_file: str):
    actions: List[str] = []

    with open(plan_file) as f:
        data = f.readlines()

    for l in data:
        if not l.startswith(";"):
            actions.append(l.strip())

    return actions


def get_action_name(action_label: str):
    """
    Converts action label from fd plan to action name stored in the dictionary.
    Example: '(pick-tower b4 b5 b3)' -> 'pick-tower(b4,b5,b3)'
    :param action_label:
    :return:
    """
    label: str = action_label[1:-1]
    tokens: List[str] = label.split()
    name: str = tokens[0]
    args: str = ",".join(tokens[1:])

    return f"{name}({args})"


def add_action_prec(controller_state: ControllerState, action: Action):
    variables = action.precondition.variables

    for var_idx, var in enumerate(variables):
        val = action.precondition.values[var_idx]
        if val != -1:
            # assert controller_state.values[var_idx][val] == 0
            controller_state.values[var_idx][val] = 1

    return controller_state


def apply_action_effect(previous_state: ControllerState, action: Action):
    """
    (n, b, n′) ∧ ¬p(n) → ¬p(n′) if p not in add(b); fwd prop
    (n, b, n′) → ¬p(n′) if p in del(b); fwd prop. neg. info
    :param previous_state:
    :param action:
    :return: next controller state
    """
    action.generate_strips()
    vars_values = deepcopy(previous_state.values)
    # for var_idx in range(len(action.add)):
    #     val = action.add[var_idx]
    #     if val == -1:
    #         var_values = vars_values[var_idx]
    #         for i in range(len(var_values)):
    #             if var_values[i] != -1:
    #                 var_values[i] = 0

    for var_idx in range(len(action.delete)):
        vals = action.delete[var_idx]
        if len(vals) > 0:
            for v in vals:
                vars_values[var_idx][v] = -1

    next_state: ControllerState = ControllerState(previous_state.variables, vars_values)
    return next_state


def compute_states(instance_dir: str):
    sas_file = f"{instance_dir}/output.sas"
    plan: List[str] = get_actions(f"{instance_dir}/sas_plan")

    initial_state, goal_state, actions, variables, mutexs = parse_sas(sas_file)
    det_actions, nd_actions = organize_actions(actions)
    n0 = get_initial_state(initial_state)
    ng = get_goal_state(goal_state)

    states: List[ControllerState] = [ng]

    previous_state = n0
    for action_label in plan:
        action_name = get_action_name(action_label)
        action = det_actions[action_name]
        previous_state = add_action_prec(previous_state, action)
        states.append(previous_state)

        next_state = apply_action_effect(previous_state, action)
        previous_state = next_state

    unique_states = set(states)
    return unique_states


if __name__ == "__main__":
    fd_path = os.path.expanduser("~/Tools/Planners/fd/fast-downward.py")
    # domain = "./output/blocksworld-ipc08/p05/asp-opt-1/deterministic_domain.pddl"
    # instance = "./benchmarking/problems/acrobatics/p01.pddl"
    # instance_path = "output/blocksworld-ipc08/p07"
    instance_path = "output/elevators/p06"
    s = "asp-opt-1"

    fd_input = [f"{SRC_ROOT}/{instance_path}/{s}/output.sas"]
    plan_output = f"{SRC_ROOT}/{instance_path}/{s}/plan.sas"
    cwd = f"{SRC_ROOT}/{instance_path}/{s}"
    plan_length, time = compute_weak_plan(fd_input, plan_output, FD_PATH, cwd)
    #
    # args = get_args()
    # folder = args["path"]
    # run(folder)
    # instance_dir = "./output/blocksworld-ipc08/p04/asp-opt-1"
    states = compute_states(instance_dir)