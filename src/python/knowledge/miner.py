
import os
from typing import List
from base.elements import Action, FONDProblem, State, Variable

class MinerKnowledge(object):

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
        constraints = [f"#program check(t). \n"]
        # parse
        var_person_alive = [i for i in self.variables if "person-alive" in i.domain[0]][0]
        var_idx = self.variables.index(var_person_alive)

        # :- state(State), holds(State, 0, 0).
        line = f':- state(t), holds(State, {var_idx}, {1}).\n'
        constraints.append(line)

        with open(self.weakplan_kb_file, "w+") as f:
            f.writelines(constraints)

        self.fond_problem.seq_kb = self.weakplan_kb_file

    def add_control_knowledge(self):
        constraints = []
        
        adjacent_positions = self.parse_pddl()
        # add adjacent positions constaints
        person_at_var = [i for i in self.variables if "person-at" in i.domain[0]][0]
        vehicle_at_var_idx = self.variables.index(person_at_var)

        for _from, _to in adjacent_positions:
            _from_term = f'Atom person-at({_from.lower()})'
            _to_term = f'Atom person-at({_to.lower()})'
            if _from_term in person_at_var.domain and _to_term in person_at_var.domain:
                _f = person_at_var.domain.index(_from_term)
                _t = person_at_var.domain.index(_to_term)
                line = f"adjacent({_f}, {_t}).\n"
                # constraints.append(line)

                line = f"adjacent({_f}, {_f}).\n"
                # constraints.append(line)

        # :- holds(S1, 1, X), not goalState(S1), {holds(S2, 1, Y): successor(S1, S2), adjacent(X, Y)} =0.
        line = f':- holds(S1, {vehicle_at_var_idx}, X), not goalState(S1), {{holds(S2, {vehicle_at_var_idx}, Y): successor(S1, S2), adjacent(X, Y)}}=0. \n'
        # constraints.append(line)

        # parse
        var_person_alive = [i for i in self.variables if "person-alive" in i.domain[0]][0]
        var_idx = self.variables.index(var_person_alive)

        # :- state(State), holds(State, 0, 0).
        line = f':- state(State), holds(State, {var_idx}, {1}).\n'
        constraints.append(line)

        # :- policy(State, Action), add(Action, 0, 0).
        line = f':- policy(State, Action), add(Action,_, {var_idx}, 1).\n'        
        constraints.append(line)

        with open(self.controller_kb_file, "w+") as f:
            f.writelines(constraints)

        self.fond_problem.controller_constraints["kb"] = self.controller_kb_file

    def parse_pddl(self):
        file = self.fond_problem.problem
        with open(file) as f:
            data = f.readlines()
        adjacent_positions = []
        for _t in data:
            if _t.strip() and "road" in _t:
                pos = _t[:-1].split(" ")
                adjacent_positions.append((pos[1], pos[2][:-1]))

        return adjacent_positions
