from typing import List
import re

re_policy_effect = r'policy\((?P<from>[\d]+),\"(?P<action>[\a-z-\(\d\,\)]+)\",\"(?P<effect>[e(\d\,\)]+)\"\)'
DUMMY_POLICY = "policy(-1,-1,-1)"

def create_backbone_constraint(backbone: List[tuple[str, str]], constraint_file: str, constraint_type = "loose"):
    """
    Backbone constraints consist of ensuring each action is taken in a policy and the sequence of actions is as per the backbone.
    For example,
    :- {policy(State, Action): state(State), Action = "move-forward-door-open_DETDUP_0(l1,l2,d2,d3)"} 0.
    :- backbone(A1, A2) :- transition(S1, A1, S2), policy(S2, A2), state(S1), state(S2), A1 = "move-forward-door-open_DETDUP_0(l1,l2,d2,d3)", A2 =  "move-forward-door-open_DETDUP_0(l2,l3,d3,d4)".

    :param backbone:
    :param constraint_file:
    :return:
    """

    if constraint_type == "loose":
        write_loose_constraints(backbone, constraint_file)
    elif constraint_type == "strict":
        write_strict_constraints(backbone, constraint_file)


def write_strict_constraints(backbone, constraint_file):
    backbone_constraints = []
    num_actions = len(backbone)
    counter = 0
    labels: List[str] = [f"A{i}" for i in range(1, num_actions + 1)]
    for (action, effect) in backbone:
        state = counter
        next_state = counter + 1

        policy_constraint = f'policy({state}, "{action}").\n'
        if next_state == len(backbone):
            transition_constraint = f'transition({state}, "{effect}", X) :- goalState(X).\n'
        else:
            transition_constraint = f'transition({state}, "{effect}", {next_state}).\n'

        counter += 1
        backbone_constraints.append(policy_constraint)
        backbone_constraints.append(transition_constraint)

    backbone_constraints.append(f"backboneState(0..{counter - 1}).\n")
    backbone_constraints.append(f"backboneState(X) :- goalState(X).\n")

    with open(constraint_file, "w") as f:
        f.writelines(backbone_constraints)


def write_loose_constraints(backbone, constraint_file):
    policy_constraints = []
    num_actions = len(backbone)
    labels: List[str] = [f"A{i}" for i in range(1, num_actions + 1)]
    for action, effect in backbone:
        policy_constraint = f':- {{policy(State, Action): state(State), Action = "{action}"}} 0.\n'
        policy_constraints.append(policy_constraint)
    backbone_constraints = []
    counter = 1
    for i in range(1, len(backbone) - 1):
        action = backbone[i - 1]
        next_action = backbone[i]
        #  :-  policy(S1,"walk-on-beam_DETDUP_0(p0,p1)"), {policy(S2, "walk-on-beam_DETDUP_0(p1,p2)"): successor(S1, S2)} 0.
        backbone_term = f':- policy(S1,"{action}"), {{policy(S2, "{next_action}"): successor(S1, S2) }} 0.\n'
        # backbone_term = f'backbone{counter} :- transition(S{i},"{action}",S{i+1}), S{i+1} < S{i} + 4, policy(S{i+1}, "{next_action}").\n'
        # cardinality_term = f":- {{backbone{counter} }} 0. \n"
        # counter += 1
        #
        backbone_constraints.append(backbone_term)
        # backbone_constraints.append(cardinality_term)
    with open(constraint_file, "w") as f:
        f.writelines(policy_constraints)
        # f.writelines(backbone_constraints)


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


def get_actions_fd(plan_file: str):
    """
    Get a list of actions as specified in the plan file
    :param plan_file:
    :return:
    """
    actions: List[str] = []
    with open(plan_file) as f:
        data = f.readlines()
    for l in data:
        if not l.startswith(";"):
            actions.append(l.strip())

    return actions

def get_backbone_asp(clingo_output: str) -> List[tuple[str, str]]:
    """
    Return a backbone with actions same as the clingo instance.
    :param sas_plan:
    :return:
    """
    backbone = []

    with open(clingo_output) as f:
        data = f.readlines()

    policy_str = None
    for i in range(len(data)):
        line = data[i]
        if "Answer" in line:
            policy_str =  data[i+1]

    # not backbone found! implies unsat
    if not policy_str:
        return backbone

    policy_tuples = policy_str.split(" ")
    policy_tuples.remove(DUMMY_POLICY)
    for _p in policy_tuples:
        result = re.match(re_policy_effect, _p)
        action = result.group("action")
        effect = result.group("effect")
        backbone.append((action, effect))

    return backbone

def get_backbone_sas(sas_plan: str):
    """
    Return a backbone with actions same as the clingo instance.
    :param sas_plan:
    :return:
    """
    backbone = []

    plan: List[str] = get_actions_fd(sas_plan)
    for action_label in plan:
        action_name = get_action_name(action_label)
        backbone.append(action_name)

    return backbone
