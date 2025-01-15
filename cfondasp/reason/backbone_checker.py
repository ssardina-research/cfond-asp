import os
import re
from typing import List
from cfondasp.reason.controller_size_estimator import get_actions, get_action_name

r_tx = r"(?P<start>[\d]+)--(?P<action>[a-z-\d,_A-Z\(\)]+)-->(?P<end>[\d]+)"


def construct_controller(asp_plan: str):
    transitions = {}
    with open(asp_plan) as f:
        data = f.readlines()

    for l in data:
        if re.match(r_tx, l):
            result = re.search(r_tx, l)
            start = int(result.group("start"))
            end = int(result.group("end"))
            action = result.group("action")

            if start not in transitions:
                transitions[start] = []

            transitions[start].append((start, action, end))

    return transitions


def get_backbone(sas_plan: str):
    backbone = []

    plan: List[str] = get_actions(sas_plan)
    for action_label in plan:
        action_name = get_action_name(action_label)
        backbone.append(action_name)

    return backbone


def get_next_state(action, txs):
    next_state = None
    for tx in txs:
        tx_action = tx[1]
        if tx_action == action:
            next_state = tx[2]
            return next_state

    return next_state


def check_backbone(backbone: List[str], transitions: dict):
    current_state = 0

    for step in range(len(backbone)):
        action = backbone[step]
        txs = transitions[current_state]

        next_state = get_next_state(action, txs)
        if next_state is not None:
            current_state = next_state
        else:
            return False

    return True


if __name__ == "__main__":
    root_dir = "./output/elevators/p03/asp-opt-1"
    asp_plan = os.path.join(root_dir, "solution.out")
    transitions = construct_controller(asp_plan)

    sas_plan = os.path.join(root_dir, "sas_plan")
    backbone = get_backbone(sas_plan)
    result = check_backbone(backbone, transitions)
    print(f"Backbone matches for {asp_plan}: {result}")