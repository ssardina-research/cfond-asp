import argparse
from pathlib import Path
from base.elements import FONDProblem
import coloredlogs
import logging
import os
import sys
import shutil
from checker.verify import verify
from utils.system_utils import get_root
from solver.asp import solve, parse, solve_with_backbone
from timeit import default_timer as timer

PYTHON_MINOR_VERSION = 10
logger: logging.Logger = None

# instance values
domain = None
problem = None
what_to_do = None
output = None
timeout = None
model = None
clingo_args_str = None
extra_kb = None
max_states = None
filter_undo = False
domain_kb = None

def init():
    # check python version
    if sys.version_info[0] < 3 or sys.version_info[1] < PYTHON_MINOR_VERSION:
        logger.error(f"Python version sould be at least 3.{PYTHON_MINOR_VERSION}")
        sys.exit(1)

    # check if clingo is in path
    if not shutil.which("clingo"):
        logger.error("Clingo not found in the path.")
        sys.exit(1)

    # create output folder if it does not exist
    if not os.path.exists(output):
        os.makedirs(output)


def get_fond_problem() -> FONDProblem:
    # determiniser. We use a recent version of FD
    root:Path = get_root()
    translator: str = os.path.join(root, "translator-fond", "translate.py")
    translator_args: str = "{domain} {instance} --sas-file {sas_file}"

    # classical planner
    classical_planner: str = os.path.join(root, "asp", "weakplanInc.lp")

    # asp tools
    clingo = "clingo"
    if clingo_args_str:
        clingo_args = clingo_args.split()
    else:
        clingo_args = []

    # set the controller model
    fond_problem = FONDProblem(domain=domain, problem=problem, root=root, sas_translator=translator, translator_args=translator_args, controller_model=model, clingo=clingo, clingo_args=clingo_args, max_states=max_states, time_limit=timeout, filter_undo=filter_undo, extra_kb=extra_kb, classical_planner=classical_planner, domain_knowledge=domain_kb)

    fond_problem.controller_constraints = {}
    
    if extra_kb:
        fond_problem.controller_constraints["extra"] = extra_kb

    if filter_undo:
        undo_constraint =os.path.join(root, "asp", "control", "undo.lp")
        fond_problem.controller_constraints["undo"] = undo_constraint
    
    return fond_problem


def main():
    global domain, problem, what_to_do, output, timeout, model, clingo_args_str, extra_kb, max_states, filter_undo, domain_kb

    # CLI options
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="High-level interface for solving and experimenting with FOND problems."
    )
    parser.add_argument("domain",
                        help="Domain PDDL file")
    parser.add_argument("problem",
                        help="Problem PDDL file")
    parser.add_argument("--max_states",
                        help="Maximum number of controller states", 
                        type=int,
                        default=100)
    parser.add_argument("--what_to_do",
                        help="Functionality of the system to execute. Currently, verification only works for strong cyclic plans.",
                        choices=["solve", "verify", "determinise", "solve-with-backbone"],
                        default="solve")
    parser.add_argument("--timeout",
                        help="timeout for solving the problem (in seconds).", 
                        type=int)
    parser.add_argument("--model",
                        help="ASP model to use for FOND",
                        choices=["fondsat", "regression"],
                        default="fondsat")
    parser.add_argument("--clingo_args",
                        help="Arguments to Clingo",
                        type=str,
                        default="")
    parser.add_argument("--extra_constraints",
                        help="Addtional asp constraints (as input file to clingo)",
                        type=str,
                        default=None)
    parser.add_argument("--filter_undo",
                        help="Filter undo actions from policy consideration.",
                        type=bool,
                        default=False)
    parser.add_argument("--domain_kb",
                        help="Add domain knowledge.",
                        choices=["blocksworld", "tireworld", "miner", "acrobatics", "spikytireworld"],
                        default=None)
    parser.add_argument("--output",
                        help="location of output folder.",
                        type=str,
                        default="./output")
    
    args = parser.parse_args()
    domain = os.path.abspath(args.domain)
    problem = os.path.abspath(args.problem)
    what_to_do = args.what_to_do
    output = os.path.abspath(args.output)
    timeout = args.timeout
    model = args.model
    clingo_args_str = args.clingo_args
    extra_kb = args.extra_constraints
    max_states = args.max_states
    filter_undo = args.filter_undo
    domain_kb = args.domain_kb

    # initialise
    init()

    start = timer()
    fond_problem = get_fond_problem()

    if what_to_do == "solve":
        solve(fond_problem, output)
    elif what_to_do == "verify":
        verify(output)
    elif what_to_do == "determinise":
        parse(fond_problem, output)
    elif what_to_do == "solve-with-backbone":
        solve_with_backbone(fond_problem, output, only_size=True)

    end = timer()
    total_time = end - start
    logger.info(f"Time(s) taken:{total_time}")
    with open(f"{output}/{what_to_do}_time.out", "w+") as f:
        f.write(f"Totaltime(s):{total_time}{os.linesep}")


if __name__ == "__main__":
    # set logger
    logger = logging.getLogger(__name__)
    coloredlogs.install(level='INFO')

    main()
