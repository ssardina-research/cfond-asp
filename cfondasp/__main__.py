import argparse
from pathlib import Path
import coloredlogs
import logging
import os
import sys
import shutil
from timeit import default_timer as timer

from .base.elements import FONDProblem
from .checker.verify import verify, build_controller
from .utils.system_utils import get_package_root
from .solver.asp import solve, parse, solve

PYTHON_MINOR_VERSION = 10
logger: logging.Logger = None

# instance values
domain = None
problem = None
mode = None
output_dir = None
timeout = None
model = None
clingo_args_str = None
extra_kb = None
max_states = None
min_states = None
inc_states = None
filter_undo = False
domain_kb = None
solution_type = "strong-cyclic"
determiniser = "fond-utils"
FD_INV_LIMIT = 300


def init():
    # check python version
    if sys.version_info[0] < 3 or sys.version_info[1] < PYTHON_MINOR_VERSION:
        logger.error(f"Python version sould be at least 3.{PYTHON_MINOR_VERSION}")
        sys.exit(1)

    # check if clingo is in path
    if not shutil.which("clingo"):
        logger.error("Clingo not found in the path.")
        sys.exit(1)

    # check if determiniser is in path
    if not shutil.which(determiniser):
        logger.error("fond-utils not found in the path.")
        sys.exit(1)

    # create output folder if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


def get_fond_problem() -> FONDProblem:
    # determiniser. We use a recent version of FD
    root: Path = get_package_root()
    translator: str = os.path.join(root, "utils", "translate", "translate.py")
    translator_args: str = (
        "{domain} {instance} --sas-file {sas_file}"
        + f" --invariant-generation-max-time {FD_INV_LIMIT}"
    )

    # classical planner
    classical_planner: str = os.path.join(root, "asp", "weakplanInc.lp")

    # asp tools
    clingo = "clingo"
    if clingo_args_str:
        clingo_args = clingo_args_str.split()
    else:
        clingo_args = []

    # set the controller model
    fond_problem = FONDProblem(
        domain=domain,
        problem=problem,
        solution_type=solution_type,
        root=root,
        determiniser=determiniser,
        sas_translator=translator,
        translator_args=translator_args,
        controller_model=model,
        clingo=clingo,
        clingo_args=clingo_args,
        max_states=max_states,
        min_states=min_states,
        inc_states=inc_states,
        time_limit=timeout,
        filter_undo=filter_undo,
        extra_kb=extra_kb,
        classical_planner=classical_planner,
        domain_knowledge=domain_kb,
    )

    fond_problem.controller_constraints = {}

    if extra_kb:
        fond_problem.controller_constraints["extra"] = os.path.abspath(extra_kb)

    if filter_undo:
        undo_constraint = os.path.join(root, "asp", "control", "undo.lp")
        fond_problem.controller_constraints["undo"] = undo_constraint

    return fond_problem


def main():
    global domain, problem, mode, output_dir, timeout, model, clingo_args_str, extra_kb, max_states, min_states, inc_states, filter_undo, domain_kb, solution_type

    logger = logging.getLogger(__name__)
    coloredlogs.install(level=logging.DEBUG)

    # CLI options
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="High-level interface for solving and experimenting with FOND problems."
    )
    parser.add_argument("domain", help="Domain PDDL file")
    parser.add_argument("problem", help="Problem PDDL file")
    parser.add_argument(
        "--max_states",
        help="Maximum number of controller states (Default: %(default)s).",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--min_states",
        help="Minimum number of controller states (Default: %(default)s).",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--inc_states",
        help="Step size of controller size iteration (Default: %(default)s).",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--mode",
        help="Functionality of the system to execute. Currently, verification only works for strong-cyclic plans (Default: %(default)s).",
        choices=["solve", "verify", "determinise"],
        default="solve",
    )
    parser.add_argument(
        "--solution_type",
        help="Select type of plan solutions the planner should look for (Default: %(default)s).",
        choices=["strong", "strong-cyclic"],
        default="strong-cyclic",
    )
    parser.add_argument(
        "--timeout", help="Timeout for solving the problem (in seconds).", type=int
    )
    parser.add_argument(
        "--model",
        help="ASP model to use for FOND (only relevant for strong-cyclic solutions) (Default: %(default)s)",
        choices=["fondsat", "regression"],
        default="fondsat",
    )
    parser.add_argument(
        "--clingo_args", help="Arguments to pass to Clingo.", type=str, default=""
    )
    parser.add_argument(
        "--extra_constraints",
        help="Additional asp constraints (as input file to Clingo)",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--filter_undo",
        help="Filter undo actions from policy consideration.",
        action="store_true",
    )
    parser.add_argument(
        "--use_backbone",
        help="Use backbone size for minimum controller size estimation.",
        action="store_true",
    )
    parser.add_argument(
        "--domain_kb",
        help="Add pre-defined domain knowledge (Default: %(default)s).",
        choices=["triangle-tireworld", "miner", "acrobatics", "spikytireworld"],
        default=None,
    )
    parser.add_argument(
        "--dump_cntrl",
        help="Save controller in text and json files.",
        action="store_true",
    )
    parser.add_argument(
        "--output",
        help="location of output folder (Default: %(default)s).",
        type=str,
        default="./output",
    )

    args = parser.parse_args()
    domain = os.path.abspath(args.domain)
    problem = os.path.abspath(args.problem)
    mode = args.mode
    output_dir = os.path.abspath(args.output)
    timeout = args.timeout
    model = args.model
    clingo_args_str = args.clingo_args.replace("'", "").replace('"', "")
    extra_kb = args.extra_constraints
    max_states = args.max_states
    min_states = args.min_states
    inc_states = args.inc_states
    filter_undo = args.filter_undo
    domain_kb = args.domain_kb
    use_backbone = args.use_backbone
    solution_type = args.solution_type
    dump_cntrl = args.dump_cntrl

    if mode == "verify" and not os.path.exists(output_dir):
        logger.error(f"Output folder does not exist, cannot verify!: {output_dir}")
        exit(1)

    # initialise
    init()

    start = timer()
    fond_problem = get_fond_problem()

    if mode == "solve":
        solve(fond_problem, output_dir, back_bone=use_backbone, only_size=True)

        if dump_cntrl:
            logger.info("Dumping controller...")
            build_controller(output_dir)
    elif mode == "verify":
        verify(output_dir)
    elif mode == "determinise":
        parse(fond_problem, output_dir)

    end = timer()
    total_time = end - start
    logger.debug(f"Output folder: {output_dir}")
    logger.warning(f"Time taken: {total_time}")
    with open(os.path.join(output_dir, f"{mode}_time.out"), "w+") as f:
        f.write(f"Total time: {total_time}\n")


if __name__ == "__main__":
    # set logger
    logger = logging.getLogger(__name__)
    coloredlogs.install(level=logging.DEBUG)

    main()
