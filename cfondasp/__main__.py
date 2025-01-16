import argparse
from pathlib import Path
import coloredlogs
import logging
import os
import sys
import shutil
from timeit import default_timer as timer

from cfondasp import VERSION
from .base.elements import FONDProblem
from .checker.verify import verify, build_controller
from .utils.system_utils import get_package_root
from .solver.asp import solve, parse, solve

PYTHON_MINOR_VERSION = 10
logger: logging.Logger = None

DEFAULT_SOL_TYPE = "strong-cyclic"
DETERMINIZER = "fond-utils"
FD_INV_LIMIT = 300


def init(args):
    # check python version
    if sys.version_info[0] < 3 or sys.version_info[1] < PYTHON_MINOR_VERSION:
        logger.error(f"Python version sould be at least 3.{PYTHON_MINOR_VERSION}")
        sys.exit(1)

    # check if clingo is in path
    if not shutil.which("clingo"):
        logger.error("Clingo not found in the path.")
        sys.exit(1)

    # check if determiniser is in path
    if not shutil.which(DETERMINIZER):
        logger.error("fond-utils not found in the path.")
        sys.exit(1)

    # create output folder if it does not exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)


def get_fond_problem(conf) -> FONDProblem:
    # determiniser. We use a recent version of FD
    root: Path = get_package_root()
    translator: str = os.path.join(root, "utils", "translate", "translate.py")
    translator_args: str = (
        "{domain} {instance} --sas-file {sas_file}"
        + f" --invariant-generation-max-time {FD_INV_LIMIT}"
    )

    # classical planner
    classical_planner: str = os.path.join(root, "asp", "weakplanInc.lp")

    # asp tools-reg
    clingo = "clingo"
    if conf.clingo_args:
        clingo_args = conf.clingo_args.split()
    else:
        clingo_args = []

    # build a full FOND problem task
    fond_problem = FONDProblem(
        domain=conf.domain,
        problem=conf.problem,
        solution_type=conf.solution_type,
        root=root,
        determiniser=DETERMINIZER,
        sas_translator=translator,
        translator_args=translator_args,
        controller_model=conf.model,
        clingo=clingo,
        clingo_args=clingo_args,
        max_states=conf.max_states,
        min_states=conf.min_states,
        inc_states=conf.inc_states,
        time_limit=conf.timeout,
        filter_undo=conf.filter_undo,
        extra_kb=conf.extra_constraints,
        classical_planner=classical_planner,
        domain_knowledge=conf.domain_kb,
    )

    fond_problem.controller_constraints = {}

    if conf.extra_constraints:
        fond_problem.controller_constraints["extra"] = os.path.abspath(
            conf.extra_constraints
        )

    if conf.filter_undo:
        undo_constraint = os.path.join(root, "asp", "control", "undo.lp")
        fond_problem.controller_constraints["undo"] = undo_constraint

    return fond_problem


def main():
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
        "--mode",
        help="Functionality of the system to execute. Currently, verification only works for strong-cyclic plans (Default: %(default)s).",
        choices=["solve", "verify", "determinise"],
        default="solve",
    )
    parser.add_argument(
        "--solution-type",
        help="Select type of plan solutions the planner should look for (Default: %(default)s).",
        choices=["strong", "strong-cyclic"],
        default=DEFAULT_SOL_TYPE,
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

    args = parser.parse_args()
    args.domain = os.path.abspath(args.domain)
    args.problem = os.path.abspath(args.problem)
    args.clingo_args = args.clingo_args.replace("'", "").replace('"', "")
    args.output_dir = os.path.abspath(args.output)

    if args.mode == "verify" and not os.path.exists(args.output_dir):
        logger.error(f"Output folder does not exist, cannot verify!: {args.output_dir}")
        exit(1)

    # initialise
    init(args)

    start = timer()
    fond_problem = get_fond_problem(args)

    if args.mode == "solve":
        solve(fond_problem, args.output_dir, back_bone=args.use_backbone, only_size=True)

        if args.dump_cntrl:
            logger.info("Dumping controller...")
            build_controller(args.output_dir)
    elif args.mode == "verify":
        verify(args.output_dir)
    elif args.mode == "determinise":
        parse(fond_problem, args.output_dir)

    end = timer()
    total_time = end - start
    logger.debug(f"Output folder: {args.output_dir}")
    logger.warning(f"Time taken: {total_time}")
    with open(os.path.join(args.output_dir, f"{args.mode}_time.out"), "w+") as f:
        f.write(f"Total time: {total_time}\n")


if __name__ == "__main__":
    main()
