
import os
from typing import List
from base.elements import Action, FONDProblem, State, Variable
import re

re_position = r"Atom position\(p(?P<number>[\d]+)\)"

class AcrobaticsKnowledge(object):

    def __init__(self, fond_problem: FONDProblem, variables: List[Variable], output_dir: str) -> None:
        self.fond_problem = fond_problem
        self.variables: List[Variable] = variables
        self.output_dir: str = output_dir
        self.controller_kb_file = f"{output_dir}/kb.lp"
        self.weakplan_kb_file = f"{output_dir}/seq_kb.lp"

    def add_knowledge(self):
        self.add_weakplan_knowledge()
        self.add_control_knowledge()

    def add_weakplan_knowledge(self):
        constraints = [f"#program check(t). {os.linesep}"]
        # parse
        relevant_vars = [i for i in self.variables if "broken-leg" in i.domain[0]]
        if len(relevant_vars) == 0:
            return
        
        var_person_alive = relevant_vars[0]
        var_idx = self.variables.index(var_person_alive)

        # :- state(State), holds(State, 0, 0).
        line = f':- state(t), holds(State, {var_idx}, {0}).{os.linesep}'
        constraints.append(line)

        with open(self.weakplan_kb_file, "w+") as f:
            f.writelines(constraints)

        self.fond_problem.seq_kb = self.weakplan_kb_file

    def add_control_knowledge(self):
        constraints = []
        # parse
        relevant_vars = [i for i in self.variables if "broken-leg" in i.domain[0]]
        if len(relevant_vars) == 0:
            return
        
        # adjacent position
        position_var = [i for i in self.variables if "position" in i.domain[0]][0]
        position_var_idx = self.variables.index(position_var)

        positions = {}
        for val in position_var.domain:
            result = re.match(re_position, val)
            pos_num = int(result.group("number"))
            positions[pos_num] = position_var.domain.index(val)

        sorted_positions = sorted(positions.keys())
        
        for _i in range(len(sorted_positions) - 1):
            i = sorted_positions[_i]
            j = sorted_positions[_i + 1]
            line = f"adjacent({positions[i]}, {positions[j]}).{os.linesep}"
            constraints.append(line)
            
            line = f"adjacent({positions[j]}, {positions[i]}).{os.linesep}"
            constraints.append(line)

            line = f"adjacent({positions[i]}, {positions[i]}).{os.linesep}"
            constraints.append(line)

        # :- holds(S1, 1, X), not goalState(S1), {holds(S2, 1, Y): successor(S1, S2), adjacent(X, Y)} =0.
        line = f':- holds(S1, {position_var_idx}, X), not goalState(S1), {{holds(S2, {position_var_idx}, Y): successor(S1, S2), adjacent(X, Y)}}=0. {os.linesep}'
        constraints.append(line)

        var_person_alive = relevant_vars[0]
        var_idx = self.variables.index(var_person_alive)
        
        # :- state(State), holds(State, 0, 0).
        line = f':- state(State), holds(State, {var_idx}, {0}).{os.linesep}'
        constraints.append(line)

        # :- policy(State, Action), add(Action, 0, 0).
        line = f':- policy(State, Action), add(Action,_, {var_idx}, 1).{os.linesep}'        
        constraints.append(line)

        with open(self.controller_kb_file, "w+") as f:
            f.writelines(constraints)

        self.fond_problem.controller_constraints["kb"] = self.controller_kb_file
