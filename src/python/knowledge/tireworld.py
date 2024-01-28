
import os
from typing import List
from base.elements import Action, FONDProblem, State, Variable

class TireworldKnowledge(object):

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
        locations_with_spare = self.parse()

        # add constraints
        # has-spare(X) :- X=1.
        # :- holds(State, 18, X), not initialState(State), not goalState(State), not has-spare(X).
        for loc, (_idx, val) in locations_with_spare.items():
            line = f'hasSpare(X) :- X={val}.\n'
            constraints.append(line)
        
        # :- query(t), holds(State, 70, X), 0< State<t, not hasSpare(X).
        line = f':- query(t), holds(State, {_idx}, X), 0<State<t, not hasSpare(X).\n'
        constraints.append(line)


        with open(self.weakplan_kb_file, "w+") as f:
            f.writelines(constraints)

        self.fond_problem.seq_kb = self.weakplan_kb_file

    def add_control_knowledge(self):
        adjacent_positions = self.parse_pddl()

        constraints = []
        
        # add adjacent positions constaints
        vehicle_at_var = [i for i in self.variables if "vehicle-at" in i.domain[0]][0]
        vehicle_at_var_idx = self.variables.index(vehicle_at_var)

        for _from, _to in adjacent_positions:
            _f = vehicle_at_var.domain.index(f'Atom vehicle-at({_from})')
            _t = vehicle_at_var.domain.index(f'Atom vehicle-at({_to})')
            line = f"adjacent({_f}, {_t}).\n"
            constraints.append(line)

            line = f"adjacent({_f}, {_f}).\n"
            constraints.append(line)

        # :- holds(S1, 1, X), not goalState(S1), {holds(S2, 1, Y): successor(S1, S2), adjacent(X, Y)} =0.
        line = f':- holds(S1, {vehicle_at_var_idx}, X), not goalState(S1), {{holds(S2, {vehicle_at_var_idx}, Y): successor(S1, S2), adjacent(X, Y)}}=0. \n'
        constraints.append(line)


        # parse
        locations_with_spare = self.parse()

        # add spare tire constraints
        # has-spare(X) :- X=1.
        # :- holds(State, 18, X), not initialState(State), not goalState(State), not has-spare(X).
        for loc, (_idx, val) in locations_with_spare.items():
            line = f'hasSpare(X) :- X={val}.\n'
            constraints.append(line)
        
        line = f':- holds(State, {_idx}, X), not initialState(State), not goalState(State), not hasSpare(X).\n'
        constraints.append(line)


        with open(self.controller_kb_file, "w+") as f:
            f.writelines(constraints)

        self.fond_problem.controller_constraints["kb"] = self.controller_kb_file

    def parse(self):
        locations_with_spare = {}
        vehicle_at_var = [i for i in self.variables if "vehicle-at" in i.domain[0]][0]
        vehicle_at_var_idx = self.variables.index(vehicle_at_var)
        relevant_vars = [i for i in self.variables if "spare-in" in i.domain[0]]
        for var in relevant_vars:
            # Atom spare-in(n2)
            loc = var.domain[0].split("spare-in(")[1][:-1]
            locations_with_spare[loc] = []

        for i in range(len(vehicle_at_var.domain)):
            # Atom vehicle-at(n0)
            loc_atom = vehicle_at_var.domain[i]
            vehicle_loc = loc_atom.split("vehicle-at(")[1][:-1]
            if vehicle_loc in locations_with_spare:
                locations_with_spare[vehicle_loc] = (vehicle_at_var_idx, i)

        return locations_with_spare
    
    def parse_pddl(self):
        file = self.fond_problem.problem
        with open(file) as f:
            data = f.readlines()

        for _l in data:
            if "(:init" in _l:
                init_str = _l
                break
        tokens = init_str.split("(")

        adjacent_positions = []
        for _t in tokens:
            if _t.strip() and "road" in _t:
                pos = _t[:-1].split(" ")
                adjacent_positions.append((pos[1], pos[2]))

        return adjacent_positions