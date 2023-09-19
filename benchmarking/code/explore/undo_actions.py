""""
Generate undo actions for different domains
:- 1 {policy(S2,A2): transition(S1, A1, A2)}.

"""
from utils.helper_sas import organize_actions
from utils.translators import parse_sas
import os


def spiky(sas_file: str, output_file: str):
    undo_actions = []
    initial_state, goal_state, actions, variables, mutexs = parse_sas(sas_file)
    det_actions, nd_actions = organize_actions(actions)

    for action_name, action in det_actions.items():
        if "loadtire" in action_name:
            undo_action = f"droptire({','.join(action.arguments)})"
            undo_actions.append([action_name, undo_action])
        elif "move-car-normal" in action_name:
            undo_action = f"move-car-normal({','.join(reversed(action.arguments))})"
            undo_actions.append([action_name, undo_action])

    with open(output_file, "w+") as f:
        for [action, undo_action] in undo_actions:
            row = f':- 1{{ policy(S2, "{action}"): transition(S1,"{undo_action}", S2), state(S1), state(S2) }}. {os.linesep}'
            f.write(row)


if __name__ == "__main__":
    sas_file = "./output/spiky-tireworld/p01/asp-1/output.sas"
    ck_file = "./output/spiky-tireworld/p01/asp-1/undo.lp"
    spiky(sas_file, ck_file)