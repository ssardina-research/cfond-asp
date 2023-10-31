import re
from typing import List
from base.config import ASP_OUT_LINE_END, ASP_OUT_DIVIDER
import networkit as nk
import copy
from base.elements import State

re_tx = r"(?P<from>[\d]+)--(?P<action>[a-z-A-Z\d_,\(\)]+),(?P<effect>e[\d]+)-->(?P<to>[\d]+)"
re_pl = r"(?P<from>[\d]+)-->(?P<action>[a-z-A-Z-_\d,\(\)]+)"


class Controller(object):
    """
    A controller represents the solution for a Fond problem.
    The underlying structure is a graph whose nodes map to states of the controller and the edges represent the transitions.
    """
    def __init__(self, solution: str, state: State):
        self._states = {}
        self._state = state
        self._initial_state_num = None
        self._goal_state_num = None
        self._transitions = {}
        self._policy = {}
        self._graph = nk.Graph(directed=True)
        # self._nodes_states = {}
        # self._states_nodes = {}
        self._edges_transition = {}
        self._edges_policy = {}
        self._parse(solution)
        self._build_graph()

    def initial_state(self) -> (int, State):
        return self._initial_state_num, self._states[self._initial_state_num]

    def goal_state(self) -> (int, State):
        return self._goal_state_num, self._states[self._goal_state_num]

    def policy(self, node_num: int) -> str:
        action = self._policy[node_num]
        return action

    def state(self, node_num: int) -> State:
        return self._states[node_num]

    def transitions(self, node_num: int, action: str):
        _transitions = []
        for (_from, _to), txs in self._transitions.items():
            if node_num == _from:
                for (_action, _effect) in txs:
                    if _action == action:
                        _transitions.append((_from, _to, _action, _effect))

        return _transitions

    def _parse(self, solution):
        """
        Parse the file containing information about the states, transitions and policy.
        The file should have a specific structure, where a state is represented by the values of different variables that hold in a state.
        For example:
        State:0
        0=0
        1=0
        2=1
        3=4
        4=3
        6=6
        8=6
        10=0

        A transition represents the determinised action, effect that takes from one state to another. For example, 17--move-car-spiky(nb14,nb15),e2-->19

        A policy links an actual domain action to a state. For example, 17-->move-car-spiky(nb14,nb15)

        :param solution: File containing the controller information
        :return:
        """
        with open(solution) as f:
            info = f.readlines()

        elements = self._extract_elements(info)

        for element in elements:
            if type(element) is str and "Initial" in element:
                self._initial_state_num = int(element.split(":")[1])

            elif type(element) is str and "goal" in element.lower():
                self._goal_state_num = int(element.split(":")[1])

            elif type(element) is list and "state" in element[0].lower():
                self._extract_states(element)

            elif type(element) is str and "transition" in element.lower():
                self._extract_transition(element)

            elif type(element) is str and "policy" in element.lower():
                self._extract_policy(element)

    def _extract_policy(self, element):
        """
        Extract a policy element from the given string
        :param element: Information about a policy element that maps state, action to successor states.
        :return:
        """
        element = element[len("policy:"):]
        result = re.match(re_pl, element)
        from_state = int(result.group("from"))
        action = result.group("action")
        self._policy[from_state] = action

    def _extract_transition(self, element):
        """
        Extract transition from the given string.
        :param element: Information about the transition that maps a state, determinised action to the next state.
        :return:
        """
        element = element[len("transition:"):]
        result = re.match(re_tx, element)
        from_state = int(result.group("from"))
        action = result.group("action")
        effect = result.group("effect")
        to_state = int(result.group("to"))
        if (from_state, to_state) not in self._transitions:
            self._transitions[(from_state, to_state)] = []
        self._transitions[(from_state, to_state)].append((action, effect))

    def _extract_states(self, elements):
        """
        Extract information about the state from the given strings.
        :param elements: Information about the variable values that hold in the given state.
        :return:
        """
        state = copy.copy(self._state)
        state_num = -1
        for e in elements:
            if "state" in e.lower():
                state_num = int(e.split(":")[1])
            else:
                tokens = e.split("=")
                var = int(tokens[0])
                val = int(tokens[1])
                state.values[var] = val

        self._states[state_num] = state

    @staticmethod
    def _extract_elements(info):
        """
        Extract the various information elements based on the used separator.
        :param info:
        :return:
        """
        info = [i.strip() for i in info]
        _answer, _init, _goal, _state, _transition, _policy = [idx for idx in range(len(info)) if ASP_OUT_DIVIDER in info[idx]]
        elements = [info[_answer - 1], info[_init - 1], info[_goal-1]]

        # extract state info
        _state_idx = [idx for idx in range(_goal + 1, _state) if "State" in info[idx]]
        for _i in range(len(_state_idx)-1):
            _start = _state_idx[_i]
            _end = _state_idx[_i+1]
            elements.append(info[_start: _end])

        # add last state
        elements.append(info[_end: _state])

        # extract transitions
        for _i in range(_state + 2, _transition):
            _t = f"Transition:{info[_i]}"
            elements.append(_t)

        # extract policy
        for _i in range(_transition + 2, _policy):
            _t = f"Policy:{info[_i]}"
            elements.append(_t)

        return elements

    def graph(self):
        return self._graph

    def edge_action(self, e, j):
        return self._edges_transition[(e, j)]

    def _build_graph(self):
        """
        Build the underlying graph and associate its elements to the domain objects.
        :return:
        """

        self._graph.addNodes(len(self._states))

        for (from_state, to_state), action in self._transitions.items():
            self._graph.addEdge(from_state, to_state)
            self._edges_transition[(from_state, to_state)] = action

        for from_state, action in self._policy.items():
            self._policy[from_state] = action

    def save_graph(self, graph_file):
        nk.writeGraph(self._graph, graph_file, nk.Format.DOT)

