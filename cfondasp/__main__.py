import argparse
from pathlib import Path
import coloredlogs
import logging
import os
import sys
import shutil
from timeit import default_timer as timer

from cfondasp import VERSION
from cfondasp.base.config import CLINGO_BIN, DEFAULT_MODEL, FD_INV_LIMIT, FILE_CONTROLLER_WEAK, FILE_INSTANCE, PYTHON_MINOR_VERSION, TRANSLATOR_BIN
from cfondasp.checker.verify import build_controller
from .base.elements import FONDProblem
from .utils.system_utils import get_package_root
from .solver.asp import solve, parse_and_translate, solve

logger: logging.Logger = None

def get_fond_problem(args) -> FONDProblem:
    # determiniser. We use a recent version of FD
    translator_args: str = (
        "{domain} {instance} --sas-file {sas_file}"
        + f" --invariant-generation-max-time {FD_INV_LIMIT}"
    )

    # classical planner model
    classical_planner: str = os.path.join(get_package_root(), "asp", FILE_CONTROLLER_WEAK)

    # asp tools-reg
    if args.clingo_args:
        clingo_args = args.clingo_args.split()
    else:
        clingo_args = []

    # build a full FOND problem task
    fond_problem = FONDProblem(
        domain=args.domain,
        problem=args.problem,
        output_dir=args.output_dir,
        sas_translator=args.translator_path,
        translator_args=translator_args,
        controller_model=args.model,
        clingo=CLINGO_BIN,
        clingo_args=clingo_args,
        max_states=args.max_states,
        min_states=args.min_states,
        inc_states=args.inc_states,
        time_limit=args.timeout,
        filter_undo=args.filter_undo,
        instance_file = os.path.join(args.output_dir, FILE_INSTANCE),
        extra_kb=args.extra_constraints,
        classical_planner=classical_planner,
        domain_knowledge=args.domain_kb,
    )

    fond_problem.controller_constraints = {}

    if args.extra_constraints:
        extra_constraints_file = os.path.abspath(args.extra_constraints)
        fond_problem.controller_constraints["extra"] = extra_constraints_file
        shutil.copy(extra_constraints_file, fond_problem.output_dir)

    if args.filter_undo:
        undo_constraint_file = os.path.join(
            get_package_root(), "asp", "control", "undo.lp"
        )
        shutil.copy(undo_constraint_file, fond_problem.output_dir)
        fond_problem.controller_constraints["undo"] = undo_constraint_file

    return fond_problem


def main():
    """Main function to run the planner. Entry point of the program."""
    # set logger
    logger = logging.getLogger(__name__)
    coloredlogs.install(level=logging.DEBUG)

    # CLI options
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=f"CFOND-ASP: A FOND planner for compact controllers via ASP. - Version: {VERSION}"
    )
    parser.add_argument("domain", help="Domain PDDL file")
    parser.add_argument("problem", help="Problem PDDL file")
    parser.add_argument(
        "--max-states",
        help="Maximum number of controller states (Default: %(default)s).",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--min-states",
        help="Minimum number of controller states (Default: %(default)s).",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--inc-states",
        help="Step size of controller size iteration (Default: %(default)s).",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--timeout", help="Timeout for solving the problem (in seconds).", type=int
    )
    parser.add_argument(
        "--model",
        help="ASP model to use for FOND (Default: %(default)s)",
        choices=["fondsat", "regression", "strong"],
        default=DEFAULT_MODEL,
    )
    parser.add_argument(
        "--clingo-args", help="Arguments to pass to Clingo.", type=str, default=""
    )
    parser.add_argument(
        "--extra-constraints",
        help="Additional asp constraints (as input file to Clingo)",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--filter-undo",
        help="Filter undo actions from policy consideration.",
        action="store_true",
    )
    parser.add_argument(
        "--use-backbone",
        help="Use backbone size for minimum controller size estimation.",
        action="store_true",
    )
    parser.add_argument(
        "--domain-kb",
        help="Add pre-defined domain knowledge (Default: %(default)s).",
        choices=["triangle-tireworld", "miner", "acrobatics", "spikytireworld"],
        default=None,
    )
    parser.add_argument(
        "--dump-cntrl",
        help="Save controller in text and json files.",
        action="store_true",
    )
    parser.add_argument(
        "--output",
        help="location of output folder (Default: %(default)s).",
        type=str,
        default="./output",
    )
    parser.add_argument(
        "--translator-path",
        help="SAS translator binary to use (Default: %(default)s).",
        default=TRANSLATOR_BIN,
        type=str,
    )
    args = parser.parse_args()
    args.domain = os.path.abspath(args.domain)
    args.problem = os.path.abspath(args.problem)
    args.clingo_args = args.clingo_args.replace("'", "").replace('"', "")
    args.output_dir = os.path.abspath(args.output)
    print(args)

    # 1. perform necessary checks before starting...

    # check python version
    if sys.version_info[0] < 3 or sys.version_info[1] < PYTHON_MINOR_VERSION:
        logger.error(f"Python version sould be at least 3.{PYTHON_MINOR_VERSION}")
        sys.exit(1)

    # check clingo is in path
    if not shutil.which(CLINGO_BIN):
        logger.error("Clingo not found in the path.")
        sys.exit(1)

    # check determiniser is in path
    if not shutil.which(args.translator_path):
        logger.error("SAS translator not found.")
        sys.exit(1)

    # create a fresh output folder
    if os.path.exists(args.output_dir):
        logger.warning(f"Output folder already exists, deleting: {args.output_dir}")
        shutil.rmtree(args.output_dir)
    os.makedirs(args.output_dir)

    # check for domain and problem files do exist
    if not os.path.exists(args.domain):
        logger.error(f"Domain file does not exist: {args.domain}")
        exit(1)
    if not os.path.exists(args.problem):
        logger.error(f"Problem file does not exist: {args.problem}")
        exit(1)

    # 2. All good to go. Next, build a whole FONDProblem object with all the info needed
    start = timer()
    fond_problem: FONDProblem = get_fond_problem(args)

    # 3. Solve the problem
    solve(fond_problem, back_bone=args.use_backbone, only_size=True)

    # 4. If requested, dump the controller
    if args.dump_cntrl:
        logger.info("Dumping controller (if problem has been solved!)...")
        build_controller(fond_problem.output_dir)

    # 5. Done! Wrap up and summary info
    end = timer()
    total_time = end - start
    logger.debug(f"Output folder: {fond_problem.output_dir}")
    logger.warning(f"Time taken: {total_time}")

    with open(os.path.join(fond_problem.output_dir, "time_taken.out"), "w+") as f:
        f.write(f"Total time: {total_time}\n")


# run all code (marcos' funny comment)

if __name__ == "__main__":
    main()
