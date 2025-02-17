import asyncio
from pathlib import Path
import shutil
import subprocess
import time
from typing import List
import logging
import coloredlogs
from async_timeout import timeout

from cfondasp.utils.system_utils import get_now, get_pkg_root


from cfondasp.base.config import (
    ASP_CLINGO_OUTPUT_PREFIX,
    DETERMINISTIC_ACTION_SUFFIX,
    FILE_BACKBONE,
    FILE_INSTANCE_WEAK,
    FILE_UNDO_ACTIONS,
    FILE_WEAK_PLAN_OUT,
)
from cfondasp.base.elements import FONDProblem, Action, Variable, State
from cfondasp.base.logic_operators import entails
from cfondasp.utils.system_utils import remove_files
from cfondasp.utils.backbone import get_backbone_asp, create_backbone_constraint
from cfondasp.utils.helper_asp import (
    write_goal,
    write_variables,
    write_mutex,
    write_goal_state,
    write_actions,
    write_initial_state,
    write_undo_actions,
)
from cfondasp.utils.helper_sas import organize_actions
from cfondasp.utils.translators import execute_sas_translator, parse_sas
from cfondasp.knowledge.blocksworld import BlocksworldKnowledge
from cfondasp.knowledge.tireworld import TireworldKnowledge
from cfondasp.knowledge.miner import MinerKnowledge
from cfondasp.knowledge.acrobatics import AcrobaticsKnowledge
from cfondasp.knowledge.spiky import SpikyTireworldKnowledge
import os

# use asyncio for the solver when timeout is specified
# NOTE: as of Jan 2025, we changed the external call to clingo to use subprocess.run instead of asyncio
#      because of a bug that leaves an unhandled exception in the event loop
#       refer to issue #83: https://github.com/ssardina-research/cfond-asp-private/issues/83
#      Seems that Python 3.12.x has a bug with asyncio
#     Said so, subprocess.run() is enough for our needs as we only need timeout to external process
#       and we don't need multiple async calls at all (one clingo at a time)
#    subprocess.run() does timeout (albeit busy-waiting, but that's OK as clingo runs for minutes)
USE_ASYNCIO = False

logger: logging.Logger = None
DEBUG_LEVEL = "INFO"
# DEBUG_LEVEL = "DEBUG"


def solve(fond_problem: FONDProblem, back_bone=False, only_size=False):
    """
    MAIN SOLVER FUNCTION FOR FONDPorblem

    1. Determinize
    2. Check if trivially solved.
    3. Generate ASP instance encoding.
    4. Handle backbone to estimate min number of controller states (if requested).
    5. Add opitmizations: filter undo, domain kb
    7. SOLVE!

    First we generate a backbone using classical planner and then use that to constrain the controller.

    :param fond_problem: FOND problem with all the info needed
    :param back_bone: Use backbone technique
    :param only_size: Only the size of the backbone is considered as a lower bound to the controller
    :return:
    """
    _logger: logging.Logger = _get_logger()
    _logger.info(
        f"Solving {fond_problem.domain} with problem {fond_problem.problem} using backbone={back_bone}."
    )

    # 1. determinise, translate to SAS and parse the SAS file
    initial_state: State = None
    goal_state: State = None
    initial_state, goal_state, det_actions, nd_actions, variables, mutexs = (
        parse_and_translate(fond_problem)
    )

    # 2. check if initial state is the goal state
    if entails(initial_state, goal_state):
        _logger.info("Goal met in the initial state!")
        _logger.info("Solution found!")
        _logger.info(f"Number of states in controller: 1")
        return

    # 3. generate ASP instance
    generate_asp_instance(
        fond_problem.instance_file,
        initial_state,
        goal_state,
        variables,
        mutexs,
        nd_actions,
        initial_state_encoding="both",
        action_var_affects=False,
    )

    min_controller_size = fond_problem.min_states
    # 4. generate weak plan for backbone if requested
    if back_bone:
        file_weak_plan: str = os.path.join(fond_problem.output_dir, FILE_INSTANCE_WEAK)
        generate_asp_instance_inc(
            file_weak_plan, initial_state, goal_state, variables, mutexs, nd_actions
        )

        clingo_inputs = [file_weak_plan, fond_problem.classical_planner]
        clingo_args = ["--stats"]
        if fond_problem.seq_kb:
            clingo_inputs.append(fond_problem.seq_kb)
        for f in clingo_inputs[1:]:  # copy all ASP files to be used in the output dir (except instance)
            shutil.copy(f, fond_problem.output_dir)
        cmd_executable = [fond_problem.clingo] + clingo_inputs + clingo_args

        asp_output_file = os.path.join(fond_problem.output_dir, FILE_WEAK_PLAN_OUT)
        with open(asp_output_file, "w") as file_out:
            # write start info on the output file for this run
            file_out = open(asp_output_file, "a")
            file_out.write(f"Time start: {get_now()}\n\n")
            file_out.write(" ".join(cmd_executable))
            file_out.write("\n")

            return_code, stdout = _run_clingo(cmd_executable, fond_problem.output_dir)

            # save the ASP run output to the ouput file (already opened above)
            file_out.write(stdout)
            file_out.write("\n\n")
            file_out.write(f"Time end: {get_now()}\n")
            file_out.write(f"Clingo return code: {return_code}\n")
            file_out.close()

            # get the backbone
            backbone: List[tuple[str, str]] = get_backbone_asp(asp_output_file)
            backbone_size = len(backbone)

        if backbone_size == 0:
            # problem is unsatisfiable
            _logger.info(
                f"Problem does not have a solution, since backbone could not be found!"
            )
            with open(os.path.join(fond_problem.output_dir, "unsat.out"), "w+") as f:
                f.write("Unsat")
            return
        else:
            min_controller_size = max(fond_problem.min_states, backbone_size)

        _logger.info(f"Backbone is of size {backbone_size}.")

        # we want to use the backbone itself too: the actions in the weak plan must be in the controller
        if not only_size:
            constraint_file = os.path.join(fond_problem.output_dir, FILE_BACKBONE)
            create_backbone_constraint(backbone, constraint_file, strict=True)
            fond_problem.controller_constraints["backbone"] = constraint_file
            shutil.copy(constraint_file, fond_problem.output_dir)

    # 5. Filter undo actions and include domain knowledge (if requested)
    if fond_problem.filter_undo:
        compile_undo_actions(fond_problem)
    if fond_problem.domain_knowledge:
        generate_knowledge(
            fond_problem,
            initial_state,
            goal_state,
            nd_actions,
            variables,
            fond_problem.domain_knowledge,
        )

    # 6. time to SOLVE the problem by the iterative process
    if fond_problem.time_limit and USE_ASYNCIO:
        # this version leaves an unhandle exception behind on the event loop!
        # https://github.com/ssardina-research/cfond-asp-private/issues/83
        # asyncio.run(solve_asp_iteratively_async(fond_problem, min_controller_size))

        # this one does not leave the hanging exception, but why?
        # https://stackoverflow.com/questions/65682221/runtimeerror-exception-ignored-in-function-proactorbasepipetransport
        asyncio.get_event_loop().run_until_complete(
            solve_asp_iteratively_async(fond_problem, min_controller_size)
        )
    else:
        solve_asp_iteratively(fond_problem, min_states=min_controller_size)
    return


async def solve_asp_iteratively_async(fond_problem, min_states):
    """Runs the function `n` times with an overall timeout of `timeout` seconds."""
    _logger: logging.Logger = _get_logger()

    time_limit = fond_problem.time_limit

    # a local function to run the function with a time limit
    async def run_with_time_limit():
        time_left = time_limit
        for num_states in range(
            min_states, fond_problem.max_states + 1, fond_problem.inc_states
        ):
            start_time = time.time()
            _logger.info(
                f"Solving with number of controller states={num_states} - Time left: {time_left:.2f}"
            )

            # write start info on the output file for this run
            asp_output_file = os.path.join(
                fond_problem.output_dir, f"{ASP_CLINGO_OUTPUT_PREFIX}{num_states}.out"
            )
            with open(asp_output_file, "w") as file_out:
                file_out = open(asp_output_file, "a")
                file_out.write(f"Time start: {get_now()}\n\n")
                file_out.write(" ".join(cmd_executable))
                file_out.write("\n")

                # now do the async run with a time limit - USE ASYNCIO!!
                return_code, stdout = await run_subprocess(cmd_executable + [f"-c numStates={num_states}"], time_left)

                # save the ASP run output to the ouput file (already opened above)
                file_out.write(stdout)
                file_out.write("\n\n")
                file_out.write(f"Time end: {get_now()}\n")
                file_out.write(f"Clingo return code: {return_code}\n")
                file_out.close()

            if stdout is None:
                _logger.warning(
                    f"No output on ASP run with {num_states} controller states?"
                )
                continue
            if "SATISFIABLE" in stdout and "UNSATISFIABLE" not in stdout:
                _logger.info("Solution found!")
                _logger.info(f"Number of states in controller: {num_states+1}")
                return True  # yes, found solution!

            # not a solution yet, keep looping with more controller states
            # if < 0, just set a minimal timeout for the next cycle
            time_left -= time.time() - start_time
            if time_left <= 0:
                time_left = 0.1

    # main process
    # ASP input files for Clingo
    input_files = [fond_problem.instance_file, fond_problem.controller_model]
    if fond_problem.domain_knowledge is not None:
        input_files.append(fond_problem.domain_knowledge)
    input_files += [
        fond_problem.controller_constraints[k]
        for k in fond_problem.controller_constraints
    ]
    # copy all ASP files to be used in the output directory (instance already there!    )
    for f in input_files[1:]:
        shutil.copy(f, fond_problem.output_dir, follow_symlinks=True)

    # build executable command and arguments (which contains number of controller states)
    cmd_executable = [fond_problem.clingo] + input_files + fond_problem.clingo_args

    try:
        await asyncio.wait_for(run_with_time_limit(), timeout=time_limit)
    except asyncio.TimeoutError as e:
        _logger.warning(f"Overall timeout reached before completing all runs: {e}")


async def run_subprocess(args, time_left):
    """Runs an external program using asyncio.
    Integrate stderr into stdout

    return both process return code and stdout
    """
    # run clingo in a separate process
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    stdout, _ = await asyncio.wait_for(process.communicate(), time_left)
    stdout = stdout.decode().strip()

    return process.returncode, stdout


def _run_clingo(cmd_executable, cwd, time_limit=float("inf")):
    """Runs an external program using asyncio.
    Integrate stderr into stdout

    return both process return code and stdout
    """
    process = subprocess.run(
        cmd_executable,
        cwd=cwd,
        # capture_output=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=time_limit if time_limit < float("inf") else None,
    )
    return_code = process.returncode
    stdout = process.stdout.decode()

    return return_code, stdout


def solve_asp_iteratively(fond_problem : FONDProblem, min_states):
    """Runs the function `n` times with an overall timeout of `timeout` seconds."""
    _logger: logging.Logger = _get_logger()

    # a local function to run the function with a time limit
    def run_with_time_limit():
        time_left = float("inf")  # default
        if fond_problem.time_limit is not None:
            time_left = fond_problem.time_limit
        for num_states in range(
            min_states, fond_problem.max_states + 1, fond_problem.inc_states
        ):
            start_time = time.time()
            _logger.info(
                f"Solving with number of controller states={num_states} - Time left: {time_left:.2f}"
            )
            asp_output_file = os.path.join(
                fond_problem.output_dir, f"{ASP_CLINGO_OUTPUT_PREFIX}{num_states}.out"
            )
            with open(asp_output_file, "w") as file_out:
                # write start info on the output file for this run
                file_out = open(asp_output_file, "a")
                file_out.write(f"Time start: {get_now()}\n\n")
                file_out.write(" ".join(cmd_executable))
                file_out.write("\n")

                # now run clingo!  - USE SUBPROCESS.RUN (not ASYNCIO!)
                return_code, stdout = _run_clingo(
                    cmd_executable + [f"-c numStates={num_states}"],
                    cwd=fond_problem.output_dir,
                    time_limit=time_left,
                )

                # save the ASP run output to the ouput file (already opened above)
                file_out.write(stdout)
                file_out.write("\n\n")
                file_out.write(f"Time end: {get_now()}\n")
                file_out.write(f"Clingo return code: {return_code}\n")
                file_out.close()

            if stdout is None:
                _logger.warning(
                    f"No output on ASP run with {num_states} controller states?"
                )
                continue
            if "SATISFIABLE" in stdout and "UNSATISFIABLE" not in stdout:
                _logger.info("Solution found!")
                _logger.info(f"Number of states in controller: {num_states+1}")
                return True  # yes, found solution!

            # not a solution yet, keep looping with more controller states
            # if < 0, just set a minimal timeout for the next cycle
            time_left -= time.time() - start_time
            if time_left <= 0:
                time_left = 0.1

        return False  # have tried all sizes and no solution found!

    # MAIN PROCESS
    # ASP input files for Clingo
    input_files = [fond_problem.instance_file, fond_problem.controller_model]
    if fond_problem.domain_knowledge is not None:
        input_files.append(fond_problem.domain_knowledge)
    input_files += [
        fond_problem.controller_constraints[k]
        for k in fond_problem.controller_constraints
    ]

    # copy all ASP files to be used in the output directory (instance already there!    )
    for f in input_files[1:]:
        shutil.copy(f, fond_problem.output_dir, follow_symlinks=True)

    # build executable command and arguments (which contains number of controller states)
    cmd_executable = [fond_problem.clingo] + input_files + fond_problem.clingo_args

    try:
        return run_with_time_limit()
    except subprocess.TimeoutExpired as e:
        _logger.error(f"Time limit reached: {e}")
        return False


def is_satisfiable(clingo_output_file: str):
    with open(clingo_output_file) as f:
        info = f.readlines()

    for _line in info:
        if "UNSATISFIABLE" in _line:
            return False
        elif "SATISFIABLE" in _line:
            return True
    return None  # should never get here


def generate_asp_instance_inc(
    file,
    initial_state,
    goal_state,
    variables,
    mutexs,
    nd_actions,
    initial_state_encoding="both",
    action_var_affects=False,
):
    """
    Write planning instance to a logic programming as an input to Clingo for incremental solving. This is currently to generate a weak plan.
    :param file: File to save the encoding
    :param initial_state: Initial state
    :param goal_state: Goal state
    :param variables: Variables
    :param mutexs: Mutually exclusive variable values (encoded as a state)
    :param nd_actions: Dictionary mapping a non-deterministic action name to its deterministic actions
    :param initial_state_encoding: Encoding for the initial state (negative, positive, or both)
    :param action_var_affects: Mapping of action name to variables it affects in add or del effects
    :return:
    """

    write_variables(file, variables)
    write_mutex(file, mutexs)
    write_initial_state(file, initial_state, encoding=initial_state_encoding)
    write_goal(file, goal_state)
    write_actions(file, nd_actions, variables, variable_mapping=action_var_affects)


def generate_asp_instance(
    file,
    initial_state,
    goal_state,
    variables,
    mutexs,
    nd_actions,
    initial_state_encoding="both",
    action_var_affects=False,
):
    """
    Write planning instance to a logic programming as an input to Clingo
    :param file: File to save the encoding
    :param initial_state: Initial state
    :param goal_state: Goal state
    :param variables: Variables
    :param mutexs: Mutually exclusive variable values (encoded as a state)
    :param nd_actions: Dictionary mapping a non-deterministic action name to its deterministic actions
    :param initial_state_encoding: Encoding for the initial state (negative, positive, or both)
    :param action_var_affects: Mapping of action name to variables it affects in add or del effects
    :return:
    """

    write_variables(file, variables)
    write_mutex(file, mutexs)
    write_initial_state(file, initial_state, encoding=initial_state_encoding)
    write_goal_state(file, goal_state)
    write_actions(file, nd_actions, variables, variable_mapping=action_var_affects)


def parse_and_translate(
    fond_problem: FONDProblem,
) -> (
    State,
    State,
    dict[str:Action],
    dict[str : List[Action]],
    list[Variable],
    list[State],
):
    """
    Returns the parsed PDDL Domain, PDDL problem, SAS initial state, SAS goal state, dictionary of deterministic and non-deterministic actions
    :param fond_problem: A Fond problem with the required inputs
    :param output_dir: Path to the output directory
    :param temp_dir: Path to the temporary directory
    :return: Parsed PDDL domain, PDDL problem, SAS initial state, SAS goal state, dictionary of deterministic actions, dictionary of non-deterministic actions
    """
    # determinise!
    from pddl import parse_domain
    from pddl.formatter import domain_to_string
    from fondutils.determizer import determinize

    # step 1. Do the all outcomes determinisation at the lifted level (will produce all outcomes domain file)
    domain_file = fond_problem.domain
    all_outcomes_domain_file = os.path.join(
        fond_problem.output_dir, f"{Path(domain_file).stem}_all_outcomes.pddl"
    )
    domain = parse_domain(domain_file)

    domain_det = determinize(
        domain, dom_suffix="", op_prefix=DETERMINISTIC_ACTION_SUFFIX
    )
    with open(all_outcomes_domain_file, "w") as f:
        f.write(domain_to_string(domain_det))

    # step 2. Use the FD SAS translator (will produce output.sas)
    sas_file = os.path.join(fond_problem.output_dir, "output.sas")
    execute_sas_translator(
        fond_problem.sas_translator,
        all_outcomes_domain_file,
        fond_problem.problem,
        fond_problem.translator_args,
        fond_problem.output_dir,
        sas_file,
        os.path.join(fond_problem.output_dir, "sas_stats.txt"),
    )

    initial_state, goal_state, actions, variables, mutexs = parse_sas(sas_file)
    det_actions, nd_actions = organize_actions(actions)

    return initial_state, goal_state, det_actions, nd_actions, variables, mutexs


def compile_undo_actions(fond_problem: FONDProblem):
    undo_controller = fond_problem.controller_constraints["undo"]
    executable_list = [
        fond_problem.clingo,
        fond_problem.instance_file,
        undo_controller,
        "--stats",
    ]
    return_code, stdout = _run_clingo(executable_list, cwd=fond_problem.output_dir)

    # save output
    output_file = os.path.join(fond_problem.output_dir, FILE_UNDO_ACTIONS)
    with open(output_file, "w") as f:
        f.write(stdout)

    # create grounded file
    grounded_undo_file = os.path.join(fond_problem.output_dir, "undo_actions.lp")
    write_undo_actions(
        output_file, grounded_undo_file, process_action_type=fond_problem.filter_undo
    )

    # replace the undo constraint with the precompiled one
    fond_problem.controller_constraints["undo"] = grounded_undo_file


def generate_knowledge(
    fond_problem, initial_state, goal_state, nd_actions, variables, domain_knowledge
):
    if domain_knowledge.lower() == "triangle-tireworld":
        kb = TireworldKnowledge(fond_problem, variables, fond_problem.output_dir)
        kb.add_knowledge()
    elif domain_knowledge.lower() == "miner":
        kb = MinerKnowledge(fond_problem, variables, fond_problem.output_dir)
        kb.add_knowledge()
    elif domain_knowledge.lower() == "acrobatics":
        kb = AcrobaticsKnowledge(fond_problem, variables, fond_problem.output_dir)
        kb.add_knowledge()
    elif domain_knowledge.lower() == "spikytireworld":
        kb = SpikyTireworldKnowledge(
            fond_problem, variables, nd_actions, fond_problem.output_dir
        )
        kb.add_knowledge()


def _get_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    coloredlogs.install(level=DEBUG_LEVEL, logger=logger)
    return logger


logger = _get_logger()
