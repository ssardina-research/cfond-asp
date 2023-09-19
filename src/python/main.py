import configparser
import argparse
from base.elements import FONDProblem
import coloredlogs
import logging
import os
from checker.verify import verify
from solver.asp import solve, parse, solve_with_backbone
from timeit import default_timer as timer

OUTPUT_DIR: str = "./"


def get_fond_problem(config: configparser.ConfigParser) -> FONDProblem:
    p_id: str = config["fond"]["id"]

    problems_dir: str = os.path.expanduser(config[WHERE]["problems"])
    rel_domain: str = os.path.expanduser(config["fond"]["domain"])
    rel_problem: str = os.path.expanduser(config["fond"]["problem"])
    domain: str = f"{problems_dir}/{rel_domain}"
    problem: str = f"{problems_dir}/{rel_problem}"

    # determiniser
    translator: str = os.path.expanduser(config[WHERE]["translator"])
    translator_args: str = os.path.expanduser(config[WHERE]["translator_args"])

    # classical planner
    classical_planner = config[WHERE].get("classical_planner", None)
    if classical_planner:
        classical_planner = os.path.expanduser(classical_planner)

    # asp tools
    clingo = os.path.expanduser(config[WHERE]["clingo"]).strip()
    clingo_args_str = os.path.expanduser(config["clingo"]["args"]).strip()
    clingo_args = clingo_args_str.split()

    # controller parameters
    max_states: int = int(config["controller"]["max_states"])
    time_limit: int = int(config["fond"]["time_limit"])
    filter_undo = False
    undo_action_type = False
    if "filter_undo_actions" in config["controller"]:
        filter_undo = config["controller"]["filter_undo_actions"].lower() == "true"
        if "undo_action_type" in config["controller"]:
            undo_action_type = config["controller"]["undo_action_type"].lower() == "true"

    domain_knowledge = config[WHERE].get("domain_knowledge", None)

    kb = config[WHERE].get("controller_kb", None)
    seq_kb = config[WHERE].get("classical_planner_kb", None)
    if kb is not None:
        kb = os.path.expanduser(kb)
    if seq_kb is not None:
        seq_kb = os.path.expanduser(seq_kb)

    # set the controller model
    controller_model = os.path.expanduser(config[WHERE]["controller_model"]).strip()
    fond_problem = FONDProblem(id=p_id, domain=domain, problem=problem, sas_translator=translator, translator_args=translator_args, controller_model=controller_model, clingo=clingo, clingo_args=clingo_args,
                    max_states=max_states, time_limit=time_limit, kb=kb, seq_kb=seq_kb, filter_undo=filter_undo, undo_action_type=undo_action_type, domain_knowledge=domain_knowledge, classical_planner=classical_planner)

    fond_problem.controller_constraints = {}

    if filter_undo:
        undo_constraint = os.path.expanduser(f'{config[WHERE]["root"]}/src/asp/control/undo.lp')
        fond_problem.controller_constraints["undo"] = undo_constraint
    return fond_problem


def parse_config(config_file: str) -> FONDProblem:
    global OUTPUT_DIR, WHERE
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(config_file)

    # set the output and temp directories
    # loc: str = config["fond"]["location"] if WHERE is None else WHERE
    WHERE = config["fond"]["location"] if WHERE is None else WHERE
    rel_output = os.path.expanduser(config["fond"]["output"])
    output_root = os.path.expanduser(config[WHERE]["output_dir"])
    output = f"{output_root}/{rel_output}"

    clingo_ref = config["clingo"]["ref"]
    OUTPUT_DIR = f"{output}/{clingo_ref}"  # add a suffix
    p_id: str = config["fond"]["id"]

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(f"{OUTPUT_DIR}/{p_id}_config.ini", "w") as f:
        config.write(f)

    # return the fond problem information
    return get_fond_problem(config)


def main():
    # set logger
    logger = logging.getLogger(__name__)
    coloredlogs.install(level='INFO')

    # CLI options
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="High-level interface for solving and experimenting with FOND problems."
    )
    parser.add_argument("config_file",
                        help="Config file with the FOND instance details.")
    parser.add_argument("what_to_do",
                        help="Functionality of the system to execute.",
                        choices=[
                        "solve", "verify", "determinise", "solve-with-backbone"])
    parser.add_argument("--where",
                        help="Where to execute the system.", 
                        type=str)
    args = parser.parse_args()
    config_file = args.config_file
    what_to_do = args.what_to_do

    global WHERE
    WHERE = args.where if args.where is not None else None

    start = timer()
    fond_problem = parse_config(config_file)
    logger.info(f"Read the config file {config_file}")


    if what_to_do == "solve":
        solve(fond_problem, OUTPUT_DIR)
    elif what_to_do == "verify":
        verify(OUTPUT_DIR)
    elif what_to_do == "determinise":
        parse(fond_problem, OUTPUT_DIR)
    elif what_to_do == "solve-with-backbone":
        solve_with_backbone(fond_problem, OUTPUT_DIR, only_size=True)

    end = timer()
    total_time = end - start
    logger.info(f"Time(s) taken:{total_time}")
    with open(f"{OUTPUT_DIR}/{what_to_do}_time.out", "w+") as f:
        f.write(f"Totaltime(s):{total_time}{os.linesep}")


if __name__ == "__main__":
    main()
