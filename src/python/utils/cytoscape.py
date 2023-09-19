"""
This script creates a csv input for cytoscape from a solution file
"""
import os
from typing import List

from utils.backbone import get_backbone_sas

SEP = ";"
EDGE_HEADERS = f"source{SEP}target{SEP}name{SEP}type{os.linesep}"


def get_transitions(solution):
    tx_info = []
    transitions = {}
    with open(solution) as f:
        data = f.readlines()

    for i in range(len(data)):
        line = data[i]
        if "Transition" in line:
            tx = data[i+1]
            tokens = tx.split("--")
            source = tokens[0]
            action = tokens[1]
            target = tokens[2][1:].strip()
            tx_info.append(f"{source}{SEP}{target}{SEP}{action}{SEP}c{os.linesep}")

            if source not in transitions:
                transitions[source] = []
            transitions[source].append((source, action, target))

    return tx_info, transitions


def compare(transitions, backbone):
    common_txs = []
    start_state = "0"
    counter = 0
    for action in backbone:
        txs = transitions[start_state]
        for tx in txs:
            if action == tx[1]:
                # common_txs.append(tx)
                common_txs.append(f"{tx[0]}{SEP}{tx[2]}{SEP}{tx[1]}{SEP}c{os.linesep}")
                start_state = tx[2]
                counter += 1

    different_txs = []
    next_state = max([int(s) for s in transitions.keys()]) + 2
    #different_txs.append(f"{counter}{SEP}{next_state}{SEP}{backbone[counter]}{SEP}b{os.linesep}")
    for i in range(counter+1, len(backbone)):
        action = backbone[i]
        different_txs.append(f"{next_state}{SEP}{next_state+1}{SEP}{action}{SEP}b{os.linesep}")
        next_state += 1

    return common_txs, different_txs


def solution_to_cytoscape(solution, plan_file, cytoscape_input):
    tx_info, transitions = get_transitions(solution)
    if plan_file:
        backbone: List[str] = get_backbone_sas(plan_file)
    else:
        backbone = [""]
    common_edges, different_edges = compare(transitions, backbone)
    different_ctrl_edges = set(tx_info).difference(set(common_edges))

    # common_txs = []
    # for c in common_edges:
    #     common_txs.append(f"{c[0]},{c[1]},{c[1]}a{os.linesep}")
    #
    # different_ctrl_txs = []
    # for c in different_ctrl_edges:
    #     different_ctrl_txs.append(f"{c[0]},{c[1]},{c[1]}c{os.linesep}")

    with open(cytoscape_input, "w") as f:
        f.write(EDGE_HEADERS)
        f.writelines(different_edges)
        f.writelines(common_edges)
        f.writelines(different_ctrl_edges)


if __name__ == "__main__":
    output_dir = "./output/tireworld/p01"
    # backbone = f"{output_dir}/asp-b-4/sas_plan"
    solution = f"{output_dir}/asp-reg-1/solution.out"
    cytoscape_input = f"{output_dir}/asp-reg-1/edges.csv"
    backbone = None
    solution_to_cytoscape(solution, backbone, cytoscape_input)
