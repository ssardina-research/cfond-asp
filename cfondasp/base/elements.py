import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass(slots=True)
class Variable(object):
    """
    A finite domain variable as per the SAS+ specification.
    Example from the blocksworld domain:
        begin_variable
            var1
            -1
            2
            Atom clear(b2)
            NegatedAtom clear(b2)
        end_variable

    The symbolic name of the variable is var1 and its domain is a list of size 2 [Atom clear(b2), NegatedAtom clear(b2)].
    """
    name: str
    domain: List[str]


@dataclass(slots=True, frozen=True)
class State(object):
    """
    A state in the planning problem. A state consists of variables along with their assigned values.
    A variable is said to be undefined in a state if its value is -1.
    A state is partial if it has an undefined variable.

    Example from the blocksworld domain:
    The domain has 11 variables [var0,...,var10].
    A possible partial state is when var2 has value Atom on(b1, b2) and rest of the variables' values are unknown.
    This state will have values [-1,...,2,...,-1] where 2 occurs at the position of var6.domain.
    """
    variables: List[Variable]
    values: List[int]

    def is_partial(self) -> bool:
        return -1 in self.values

    def __eq__(self, state) -> bool:
        return self.values == state.values

    def __copy__(self):
        state = State(variables=self.variables, values=self.values[:])
        return state

    def __hash__(self):
        return hash(tuple(self.values))

    def __str__(self):
        """
        String representation of the state for readability. Only the known values are used.
        :return:
        """
        _repr = []
        for idx, val in enumerate(self.values):
            if val >= 0:  # if val is -1 we don't need to show it
                value: str = self.variables[idx].domain[val].replace("Atom ", "").replace("Negated", "not ")
                _repr.append(value)

        return ",".join(_repr)

    def str__prop(self):
        """
        String representation of the state as propositions.
        :return:
        """
        _repr = []
        for idx, val in enumerate(self.values):
            if val >= 0:  # if val is -1 we don't need to show it
                _repr.append(f"(var{idx}={val})")

        return ",".join(_repr)

    def __repr__(self):
        return self.__str__()

    def variable_defined(self, var_idx: int):
        return self.values[var_idx] != -1


@dataclass()
class Action(object):
    """
    An action is an operator in the SAS+ domain. An action has a name, list of arguments, a precondition for the action to be valid, and effects induced by the action.
    By default, the cost of executing an action is 1.
    We represent precondition and effects using State objects. Generally, the precondition and effects will be partial states.

    Example from the blocksworld domain:
    begin_operator
        put-on-block_DETDUP_1 b1 b4
        1                               # (this denotes number of preconditions)
        3 0                             # (precondition)
        3                               # (this denotes number of effects)
        0 0 -1 0                        # (effect 1)
        0 5 -1 0                        # (effect 2)
        0 6 0 6                         # (effect 3)
        0
    end_operator

    The name of the action is put-on-block_DETDUP_1 with arguments b1 and b4. The precondition is that var3 should have value 0 (i.e., Atom clear(b4)).
    There are three effects:
    1. var0 can have any previous value and the next value will be 0 (i.e., Atom clear(b1))
    2. var5 can have any previous value and the next value will be 0 (i.e., Atom emptyhand())
    3. var6 can should have previous value of 0 (i.e., Atom holding(b1)) and next value will be 6 (i.e., Atom on-table(b1))

    This operator will have the following action representation:
    name: put-on-block_DETDUP_1
    prefix_name: put-on-block
    arguments: [b1, b4]
    preconditions: A partial state with values [-1, -1, -1, 0, -1, -1, 0, -1, ..., -1]
    effects: [s1] where s1 is a partial state with values [0, -1, -1, -1, -1, 0, 6, -1, ..., -1]

    Note: The preconditions from effects are lifted to the preconditions for the action (see, e.g., effect 3 above).
    TODO: Add support for conditional effects.
    """
    name: str
    prefix_name: str
    arguments: List[str]
    precondition: State
    effects: List[State]
    add = []
    delete = []
    cost: int = 1

    def __hash__(self):
        return hash(f"{self.prefix_name}({','.join(self.arguments)})")

    def is_nondeterministic(self):
        return len(self.effects) > 1

    def __str__(self):
        return f"{self.name}({','.join(self.arguments)})"

    def __str_prefix__(self):
        return f"{self.prefix_name}({','.join(self.arguments)})"

    def strips_repr(self):
        action_name: str = self.__str__()
        prec: str = self.precondition.str__prop()
        add_list: [] = [f"(var{idx}={self.add[idx]})" for idx in range(len(self.add)) if self.add[idx] != -1]
        del_list = []
        for i in range(len(self.precondition.variables)):
            dels = self.delete[i]
            if len(dels) > 0:
                del_list += [f"(var{i}={j})" for j in dels]
        return f"name:{action_name}\nprec:{prec}\nadd:{add_list}\ndel:{del_list}"

    def __repr__(self):
        return self.__str__()

    def __repr_prefix__(self):
        return self.__str_prefix__()

    def generate_strips(self):
        """
        This assumes that the action is deterministic.
        The add list is directly generated from the effect.
        Delete list is a list of values for each variable.
         - If a variable is in the effect and precondition, then that value is added to the delete list.
         - If a variable is in the effect and not in precondition, then all other values are added to the delete list.
        :return: None
        """
        assert len(self.effects) == 1, "The action should have a single effect."

        effect: State = self.effects[0]
        self.add = effect.values  # add list is same as the effect

        self.delete = [[]] * len(effect.variables)
        for var_idx in range(len(effect.variables)):
            var: Variable = effect.variables[var_idx]
            val: int = effect.values[var_idx]

            if val != -1 and self.precondition.variable_defined(var_idx):  # If a variable is in the effect and precondition, then that value is added to the delete list.
                self.delete[var_idx] = [self.precondition.values[var_idx]]
            elif val != -1 and not self.precondition.variable_defined(var_idx):  # If a variable is in the effect and not in precondition, then all other values are added to the delete list.
                other_values = [i for i in range(len(var.domain)) if i != val]
                self.delete[var_idx] = other_values


@dataclass(slots=True)
class SASProblem(object):
    """
    A SAS problem consists of variables, initial state, goal state and actions.
    We do not store (or generate) the complete state space.
    Actions are stored indexed by their name and arguments.
    """
    variables: List[Variable]
    initial: State
    goal: State
    actions: dict[str: dict[tuple[str]: Action]]


@dataclass(slots=True)
class FONDProblem(object):
    domain: str
    problem: str
    root: str
    sas_translator: str
    translator_args: str
    controller_model: str
    clingo: str
    clingo_args: List[str]
    max_states: int = 1
    min_states: int = 1
    inc_states: int = 1
    time_limit: int = 300
    extra_kb: str = None
    filter_undo: bool = False
    classical_planner: str = None
    domain_knowledge: str = None
    controller_constraints: dict[str: str] = None
    seq_kb: str = None # use for weak plans (sequential knowledge base)

