
import os
from typing import List
from base.elements import Action, FONDProblem, State, Variable

class BlocksworldKnowledge(object):

    def __init__(self, fond_problem: FONDProblem, goal_state: State, variables: List[Variable], output_dir: str) -> None:
        self.fond_problem = fond_problem
        self.goal: State = goal_state
        self.variables: List[Variable] = variables
        self.output_dir: str = output_dir
        self.controller_kb_file = f"{output_dir}/kb.lp"
        self.weakplan_kb_file = f"{output_dir}/seq_kb.lp"

    def add_knowledge(self):
        self.add_weakplan_knowledge()
        self.add_control_knowledge()

    def add_weakplan_knowledge(self):
        # parse
        on_table, on_blocks, clear = self.parse()
        counter = 0
        constraints = [f"#program check(t). \n"]

        for _on, (var, val) in on_table.items():
            counter += 1
            # subgoal(1).
            constraint = f"subgoal({counter}).\n"
            constraints.append(constraint)

            # first subgoal
            subgoal_num = 1
            constraint = f"subgoal(State, {subgoal_num}, {counter}) :- holds(State, {var}, {val}), State=t.\n"
            constraints.append(constraint)
            subgoal_num += 1
            next_block = _on
            while next_block not in clear:
                _block, var, val = on_blocks[next_block]

                # subgoal(State, 2, 1) :- subgoal(State, 1, 1), holds(State, 8, 5), State=t.
                constraint = f"subgoal(State, {subgoal_num}, {counter}) :- subgoal(State, {subgoal_num - 1}, {counter}), holds(State, {var}, {val}), State=t.\n"
                constraints.append(constraint)
                next_block = _block
                subgoal_num += 1

            # last subgoal
            var, val = clear[next_block]
            # subgoal(State, 7, 1) :- subgoal(State, 6, 1), holds(State, 5, 0), State=t.
            constraint = f"subgoal(State, {subgoal_num}, {counter}) :- subgoal(State, {subgoal_num - 1}, {counter}), holds(State, {var}, {val}), State=t.\n"
            constraints.append(constraint)


        constraint = f":- query(t), subgoal(State1, G1, X), G1>1, {{ subgoal(State2, G2, X): G2 < G1, State2 <= State1 }} 0.\n"
        constraints.append(constraint)
        
        with open(self.weakplan_kb_file, "w+") as f:
            f.writelines(constraints)

        self.fond_problem.seq_kb = self.weakplan_kb_file

    def add_control_knowledge(self):
        # parse
        on_table, on_blocks, clear = self.parse()
        counter = 0
        constraints = []
        goal_sequence = []
        for _on, (var, val) in on_table.items():
            counter += 1
            # subgoal(1).
            constraint = f"subgoal({counter}).\n"
            constraints.append(constraint)

            # first subgoal
            subgoal_num = 1
            constraint = f"subgoal(State, {subgoal_num}, {counter}) :- holds(State, {var}, {val}).\n"
            constraints.append(constraint)
            subgoal_num += 1
            next_block = _on
            while next_block not in clear:
                _block, var, val = on_blocks[next_block]

                # subgoal(State, 2, 1) :- subgoal(State, 1, 1), holds(State, 8, 5).
                constraint = f"subgoal(State, {subgoal_num}, {counter}) :- subgoal(State, {subgoal_num - 1}, {counter}), holds(State, {var}, {val}).\n"
                constraints.append(constraint)
                next_block = _block
                subgoal_num += 1

            # last subgoal
            var, val = clear[next_block]
            # subgoal(State, 7, 1) :- subgoal(State, 6, 1), holds(State, 5, 0).
            goal_sequence.append(subgoal_num)
            constraint = f"subgoal(State, {subgoal_num}, {counter}) :- subgoal(State, {subgoal_num - 1}, {counter}), holds(State, {var}, {val}).\n"
            constraints.append(constraint)


        constraint = f":- subgoal(State1, G1, X), G1>1, {{ subgoal(State2, G2, X): G2 < G1, State2 <= State1 }} 0.\n"
        constraints.append(constraint)

        for i in range(len(goal_sequence)-1):
            # :- subgoal(State1, 6, 1), subgoal(State2, 3, 2), State1 > State2.
            _i = goal_sequence[i]
            _j = goal_sequence[i+1]
            constraint = f":- subgoal(State1, {_i}, {i+1}), subgoal(State2, {_j}, {i+2}), State1 > State2.\n"
            constraints.append(constraint)
        
        with open(self.controller_kb_file, "w+") as f:
            f.writelines(constraints)

        self.fond_problem.controller_constraints["kb"] = self.controller_kb_file

    def parse(self):
        on_table = {}
        on_blocks = {}
        clear = {}
        relevant_vars = [i for i in range(len(self.goal.values)) if self.goal.values[i] >= 0]
        for var in relevant_vars:
            val = self.goal.values[var]
            condition = self.variables[var].domain[val]
            if "clear" in condition:
                # condition = Atom clear(b1)
                _i = condition.index("(") + 1
                _j = condition.index(")")
                b1 = condition[_i:_j]
                clear[b1] = (var, val)
            elif "table" in condition:
                # condition = Atom on-table(b1)
                _i = condition.index("(") + 1
                _j = condition.index(")")
                b1 = condition[_i:_j]
                on_table[b1] = (var, val)

            elif "on" in condition:
                # condition = Atom on(b1,b3)
                _i = condition.index("(") + 1
                _j = condition.index(")")
                b1, b2 = condition[_i:_j].split(",")
                on_blocks[b2.strip()] = (b1.strip(), var, val)

        return on_table, on_blocks, clear