import argparse
import copy
import json
import logging
import os
import queue
import coloredlogs
import re
from base.config import ASP_CLINGO_OUTPUT_PREFIX, ASP_OUT_LINE_END, DETERMINISTIC_ACTION_SUFFIX, ASP_EFFECT_TERM
from base.elements import State, FONDProblem, Variable, Action
from base.logic_operators import entails, progress
from checker.controller import Controller
from utils.asp_output import parse_clingo_output
from utils.helper_sas import organize_actions
from utils.translators import parse_sas
import networkit as nk

re_file_name = r"clingo_out_(?P<idx>[\d]+).out"

CONTROLLER_TXT_FILE = 'controller.out'
CONTROLLER_JSON_FILE = 'controller.json'
SAS_FILE = 'output.sas'
VERIFY_OUT = 'verify.out'

class SolutionSpace(object):
    def __init__(self, controller_node, domain_state, nd_actions, controller):
        self._initial_controller_node = controller_node
        self._initial_planning_state = domain_state
        self._controller = controller
        self._nd_actions = nd_actions
        self._controller_nodes = {}
        self._nodes_planning_states = {}
        self._planning_states_nodes = {}
        self._graph = nk.Graph(directed=True)
        self._initialise()

    def progress(self, controller_node, action, transitions):
        # get the corresponding internal graph node
        node = self._controller_nodes[controller_node]

        # get the planning state associated with this node
        planning_state = self._nodes_planning_states[node]

        new_nodes = []

        # apply the action to planning state
        actions = self._nd_actions[action]
        for action in actions:
            effect = self.get_effect(action)

            next_planning_state = progress(planning_state, action, 0)
            next_controller_node = self.get_next_controller_node(transitions, effect)
            next_controller_state = self._controller.state(next_controller_node)
            assert next_controller_node is not None
            assert entails(next_planning_state, next_controller_state)

            if next_controller_node not in self._controller_nodes:
                new_node = self._graph.addNode()
                self._controller_nodes[next_controller_node] = new_node
                self._nodes_planning_states[new_node] = next_planning_state
                self._planning_states_nodes[next_planning_state] = new_node

            new_node = self._controller_nodes[next_controller_node]
            new_nodes.append(new_node)
            self._graph.addEdge(node, new_node)

        return new_nodes

    def is_strong_cyclic(self, goal_node):
        dg = nk.distance.APSP(self._graph)
        max_nodes = self._graph.numberOfNodes()
        dg.run()
        target_node = self._controller_nodes[goal_node]
        for node in self._graph.iterNodes():
            distance_to_goal = dg.getDistance(node, target_node)
            if distance_to_goal > max_nodes:
                return False
        return True

    def _initialise(self):
        initial_node = self._graph.addNode()
        self._controller_nodes[self._initial_controller_node] = initial_node
        self._nodes_planning_states[initial_node] = self._initial_planning_state
        self._planning_states_nodes[self._initial_planning_state] = initial_node

    @staticmethod
    def get_effect(action):
        if DETERMINISTIC_ACTION_SUFFIX.lower() not in action.name.lower():
            return f"{ASP_EFFECT_TERM}1"
        else:
            effect_num = int(action.name.lower().split(DETERMINISTIC_ACTION_SUFFIX.lower())[1]) + 1
            return f"{ASP_EFFECT_TERM}{effect_num}"

    @staticmethod
    def get_next_controller_node(transitions, effect):
        for (_from, _to, _action, _effect) in transitions:
            if _effect == effect:
                return _to

    # @staticmethod
    # def get_action_name(action: Action):
    #     asp_args: str = (','.join(action.arguments))
    #     if len(action.arguments) > 0:
    #         action_name = f'{action.name}({asp_args})'
    #     else:
    #         action_name = f'{action.name}()'
    #
    #     return action_name


def execute_controller(controller: Controller, planning_state: State, nd_actions: dict):
    initial_node, initial_state = controller.initial_state()
    goal_node, goal_state = controller.goal_state()
    assert entails(planning_state, initial_state)
    solution_space = SolutionSpace(initial_node, planning_state, nd_actions, controller)

    open_nodes = queue.Queue()
    open_nodes.put(initial_node)
    closed_nodes = set()
    while not open_nodes.empty():
        node = open_nodes.get()
        if node not in closed_nodes:
            closed_nodes.add(node)

            if node != goal_node:
                action = controller.policy(node)
                transitions = controller.transitions(node, action)
                next_nodes = solution_space.progress(node, action, transitions)
                [open_nodes.put(i) for i in next_nodes]

    return solution_space


def add_variable_info(variables: list[Variable], solution_file: str):
    """add variable info to the output file

    Args:
        variables (list[Variable]): variables to add
        sol_file (_type_): solution file
    """
    info = [f"DomainVariables:{os.linesep}"]
    for var in variables:
        name = var.name
        domain = var.domain
        values = [d.replace("Atom", "").replace("Negated", "-").strip() for d in domain]
        info.append(f"{name}: {values}{os.linesep}")

    with open(solution_file, "a+") as f:
        f.writelines(info)


def save_controller(controller: Controller, state_variables: dict, variables: list[Variable], controller_file: str):
    data = {"nodes": [], "edges": []}
    initial_state, _ = controller.initial_state()
    goal_state, _ = controller.goal_state()

    for n in controller.graph().iterNodes():
        state = controller.state(n)

        state_type = 1
        if n == initial_state:
            state_type = 0
        elif n == goal_state:
            state_type = 2

        clingo_state = [f"var{i}={j}" for (i, j) in state_variables[n]]
        clingo_text = [f"{variables[i].name}={variables[i].domain[j].replace('Atom', '').replace('Negated', 'not').strip()}" for (i, j) in state_variables[n]]
        data["nodes"].append({"id": str(n), "label": str(n), "type": state_type, "state": str(state), "clingo": ",".join(clingo_state), "sas": ",".join(clingo_text)})

    for e, j in controller.graph().iterEdges():
        action = controller.edge_action(e, j)
        data["edges"].append({"source": str(e), "target": str(j), "label": action})

    with open(controller_file, "w+") as f:
        f.write(json.dumps(data, indent=4))


def build_controller(output_dir: str):
    """Reads an ASP model and SAS file and produces controller solution files in txt and json format.

    Args:
        output_dir (str): output of a solver run

    Returns:
        tuple: controller, initial state, and ND actions
    """
    sas_file: str = os.path.join(output_dir, SAS_FILE)
    solution_file: str = os.path.join(output_dir, CONTROLLER_TXT_FILE)
    controller_file = os.path.join(output_dir, CONTROLLER_JSON_FILE)
    last_clingo_out_file = os.path.join(output_dir, _get_last_output_file(output_dir))

    if _timed_out(last_clingo_out_file):
        _logger = _get_logger()
        _logger.warning(f"Solution timed out, cannot build controller: {last_clingo_out_file}")
        return None, None, None

    # produce first part of solution controller file by parsing the answer model found in the the (last) clingo out file
    state_variables = parse_clingo_output(last_clingo_out_file, solution_file)

    # extract data from SAS file
    initial_state, goal_state, actions, variables, mutexs = parse_sas(sas_file)
    det_actions, nd_actions = organize_actions(actions)

    # add variable info to the solution controller file
    add_variable_info(variables, solution_file)

    sample_state: State = copy.copy(initial_state)
    for i in range(len(sample_state.values)):
        sample_state.values[i] = -1

    controller: Controller = Controller(solution_file, sample_state)

    # save the graph into a controller JSON file
    save_controller(controller, state_variables, variables, controller_file)

    return controller, initial_state, nd_actions


def _get_last_output_file(output_dir) -> str:
    files = os.listdir(output_dir)
    clingo_output_files = [f for f in files if ASP_CLINGO_OUTPUT_PREFIX in f]
    ids = [_get_file_id(f) for f in clingo_output_files]
    last_id = ids.index(max(ids))
    return clingo_output_files[last_id]


def _get_file_id(f: str) -> int:
    result = re.match(re_file_name, f)
    idx = int(result.group("idx"))
    return idx


def _timed_out(output_file: str) -> bool:
    with open(output_file) as f:
        info = f.readlines()

    for _l in info:
        if "timed out" in _l.lower():
            return True

    return False

def verify(output_dir: str):
    _logger = _get_logger()

    last_clingo_out_file = os.path.join(output_dir, _get_last_output_file(output_dir))
    if not _timed_out(last_clingo_out_file):

        # build controller from ASP model and SAS file (write controller to txt and json files)
        controller, initial_state, nd_actions = build_controller(output_dir)
        goal_node, _ = controller.goal_state()

        solution_space = execute_controller(controller, initial_state, nd_actions)
        sound = solution_space.is_strong_cyclic(goal_node)

        timed_out = False
        _logger.info(f"Solution is sound? {sound}")
    else:
        sound = True
        timed_out = True
        _logger.info(f"Solution is sound? {sound} because of time out.")

    output_file = os.path.join(output_dir, VERIFY_OUT)
    with open(output_file, "w") as f:
        f.write(f"Solution is sound: {sound}{os.linesep}")
        f.write(f"Timed Out: {timed_out}")


def _get_logger() -> logging.Logger:
    logger = logging.getLogger("FondASP")
    coloredlogs.install(level='DEBUG')
    return logger


#  Does not work as a script alone as it is dependent on modules
# if __name__ == "__main__":
#     # CLI options
#     parser: argparse.ArgumentParser = argparse.ArgumentParser(
#         description="Verify a solution already produced."
#     )
#     parser.add_argument("output_folder",
#         help="Path to output directory were files were saved.")
#     parser.add_argument("--sas_file",
#         type=str,
#         default=SAS_FILE,
#         help="Path to SAS output file (Default: %(default)s).")
#     parser.add_argument("--solution_file",
#         type=str,
#         default=CONTROLLER_TXT_FILE,
#         help="Path to controller solution file (Default: %(default)s).")

#     args = parser.parse_args()

#     solution_file = os.path.join(args.output_folder, args.solution_file)
#     sas_file = os.path.join(args.output_folder, args.sas_file)

#     is_solution = verify_solution(solution_file, sas_file)
#     print(f"Controller is a solution? {is_solution}")
