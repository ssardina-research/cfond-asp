import logging
import sys
from typing import List
import os
import coloredlogs
import main
from main import parse_config
from solver.asp import parse
from utils.backbone import get_backbone
from utils.fd import compute_weak_plan

CONFIG = "asp-opt-1"
INFO = [f"scenario,instance,size{os.linesep}"]
CSV_FILE = None


def process_scenarios(location: str):
    global INFO
    scenarios = [f.name for f in os.scandir(location) if f.is_dir()]
    for d in scenarios:
        scenario_dir = f"{location}/{d}/{CONFIG}"
        instances = [f for f in os.listdir(scenario_dir)]
        for i in instances:
            min_size = get_min_controller_size(f"{scenario_dir}/{i}")
            INFO.append(f"{d},{i},{min_size}{os.linesep}")


def get_min_controller_size(config_file: str):
    fond_problem = parse_config(config_file)
    logger.info(f"Read the config file {config_file}")

    # Determinise
    output_dir = main.OUTPUT_DIR
    parse(fond_problem, output_dir)

    # use the output.sas as input to the classical planner
    fd_input = [f"{output_dir}/output.sas"]
    cwd = f"{output_dir}"
    fd_path = fond_problem.classical_planner
    compute_weak_plan(fd_input, fd_path, cwd)  # the plan is saved in a file called sas_plan

    # get the backbone
    plan_file = f"{output_dir}/sas_plan"
    backbone: List[str] = get_backbone(plan_file)

    return len(backbone) + 1


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    coloredlogs.install(level='INFO')
    location = sys.argv[1]
    out_dir = sys.argv[2]
    CSV_FILE = f"{out_dir}/weakplan.csv"
    process_scenarios(location)


