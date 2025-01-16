"""
Extract input properties from instances such as number of variables, actions, etc
"""
import logging
import os

import coloredlogs

from main import parse_config
from cfondasp.solver.asp import parse

OUTPUT_DIR: str = "./"
OUTPUT_FILE = "./output/props.csv"


def _get_logger():
    logger = logging.getLogger("InputProperties")
    coloredlogs.install(level='DEBUG')
    return logger


_logger = _get_logger()


def extract_properties(config: str):
    fond_problem = parse_config(config)
    initial_state, goal_state, det_actions, nd_actions, variables, mutexs = parse(fond_problem, OUTPUT_DIR)
    num_variables = len(variables)
    num_det_actions = 0
    num_nd_actions = 0
    for a_name, a_list in nd_actions.items():
        if len(a_list) == 1:
            num_det_actions += 1
        else:
            num_nd_actions += 1

    return num_variables, num_det_actions, num_nd_actions


def extract(folder: str):
    data = ["scenario,instance,num_variables,num_det_actions,num_nd_actions\n"]
    scenarios = os.listdir(folder)
    for scenario in scenarios:
        scenario_path = os.path.join(folder, scenario)
        config_folders = os.listdir(scenario_path)
        _logger.info(f"Processing scenario {scenario}.")
        for s in config_folders:
            if "asp" in s:
                solver_path = f"{scenario_path}/{s}"
                files = os.listdir(solver_path)
                config_files = sorted([f for f in files if f.endswith("ini")])
                for c in config_files:
                    instance = c.split("_")[0]
                    num_variables, num_det_actions, num_nd_actions = extract_properties(os.path.join(solver_path, c))
                    data.append(f"{scenario},{instance},{num_variables},{num_det_actions},{num_nd_actions}\n")
            continue

    with open(OUTPUT_FILE, "w") as f:
        f.writelines(data)


if __name__ == "__main__":
    extract("./benchmarking/configs")
    # extract_properties("./configs/acrobatics.ini")
