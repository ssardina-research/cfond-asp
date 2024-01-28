
import os
from typing import List
from base.elements import Action, FONDProblem, State, Variable

class SpikyTireworldKnowledge(object):

    def __init__(self, fond_problem: FONDProblem, variables: List[Variable], nd_actions, output_dir: str) -> None:
        self.fond_problem = fond_problem
        self.variables: List[Variable] = variables
        self.output_dir: str = output_dir
        self.nd_actions = nd_actions
        self.controller_kb_file = f"{output_dir}/kb.lp"
        self.weakplan_kb_file = f"{output_dir}/seq_kb.lp"

    def add_knowledge(self):
        # self.add_weakplan_knowledge()
        self.add_control_knowledge()

    def add_weakplan_knowledge(self):
        constraints = [f"#program check(t). \n"]
        # parse
        not_has_spare = [i for i in self.variables if "not-hasspare" in i.domain[0]][0]
        var_idx = self.variables.index(not_has_spare)


        line = f':- state(State), State=t, holds(State, {var_idx}, {0}), policy(State, A), actionType(A, "move-car-spiky").\n'
        constraints.append(line)

        with open(self.weakplan_kb_file, "w+") as f:
            f.writelines(constraints)

        self.fond_problem.seq_kb = self.weakplan_kb_file

    def add_control_knowledge(self):
        constraints = []
        # parse
        not_has_spare = [i for i in self.variables if "not-hasspare" in i.domain[0]][0]
        var_idx = self.variables.index(not_has_spare)

        # :- state(State), holds(State, 0, 0).
        for _name, _action in self.nd_actions.items():
            if "move-car-spiky" in _name:
                line = f':- state(State), holds(State, {var_idx}, {0}), policy(State, "{_name}").\n'
                constraints.append(line)
        # line = f':- state(State), holds(State, {var_idx}, {0}), policy(State, A), actionType(A, "move-car-spiky").\n'
        # constraints.append(line)

        with open(self.controller_kb_file, "w+") as f:
            f.writelines(constraints)

        self.fond_problem.controller_constraints["kb"] = self.controller_kb_file
