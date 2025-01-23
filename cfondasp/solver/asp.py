import asyncio
from pathlib import Path
import shutil
import subprocess
import time
from typing import List
import logging
import coloredlogs
from async_timeout import timeout

from cfondasp.utils.system_utils import get_now, get_package_root


from cfondasp.base.config import ASP_CLINGO_OUTPUT_PREFIX, DETERMINISTIC_ACTION_SUFFIX, FILE_BACKBONE, FILE_INSTANCE, FILE_INSTANCE_WEAK, FILE_WEAK_PLAN_OUT
from cfondasp.base.elements import FONDProblem, Action, Variable, State
from cfondasp.base.logic_operators import entails
from cfondasp.utils.system_utils import remove_files
from cfondasp.utils.backbone import get_backbone_asp, create_backbone_constraint
from cfondasp.utils.helper_asp import write_goal, write_variables, write_mutex, write_goal_state, write_actions, write_initial_state, write_undo_actions
from cfondasp.utils.helper_sas import organize_actions
from cfondasp.utils.translators import execute_sas_translator, parse_sas
from cfondasp.knowledge.blocksworld import BlocksworldKnowledge
from cfondasp.knowledge.tireworld import TireworldKnowledge
from cfondasp.knowledge.miner import MinerKnowledge
from cfondasp.knowledge.acrobatics import AcrobaticsKnowledge
from cfondasp.knowledge.spiky import SpikyTireworldKnowledge
import os

# use asyncio for the solver when timeout is specified
USE_ASYNCIO = False

logger: logging.Logger = None
DEBUG_LEVEL = "INFO"

def solve(fond_problem: FONDProblem, back_bone=False, only_size=False):
    """
    Main solver function for FOND problems.

    First we generate a backbone using classical planner and then use that to constrain the controller.

    :param fond_problem: FOND problem with all the info needed
    :param back_bone: Use backbone technique
    :param only_size: Only the size of the backbone is considered as a lower bound to the controller
    :return:
    """
    _logger: logging.Logger = _get_logger()
    _logger.info(f"Solving {fond_problem.domain} with problem {fond_problem.problem} using backbone={back_bone}.")

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
        return

    # 3. generate ASP instance
    generate_asp_instance(fond_problem.instance_file, initial_state, goal_state, variables, mutexs, nd_actions, initial_state_encoding="both", action_var_affects=False)

    min_controller_size = fond_problem.min_states
    # 4. generate weak plan for backbone if requested
    if back_bone:
        file_weak_plan: str = os.path.join(fond_problem.output_dir, FILE_INSTANCE_WEAK)
        generate_asp_instance_inc(file_weak_plan, initial_state, goal_state, variables, mutexs, nd_actions)

        clingo_inputs = [fond_problem.classical_planner, file_weak_plan]
        args = ["--stats"]
        out_file = os.path.join(fond_problem.output_dir, FILE_WEAK_PLAN_OUT)
        if fond_problem.seq_kb:
            clingo_inputs.append(fond_problem.seq_kb)

        shutil.copy(fond_problem.classical_planner, fond_problem.output_dir)
        execute_asp(
            fond_problem.clingo, args, clingo_inputs, fond_problem.output_dir, out_file
        )

        # get the backbone
        backbone: List[tuple[str, str]] = get_backbone_asp(out_file)
        backbone_size = len(backbone)

        if backbone_size == 0:
            # problem is unsatisfiable
            _logger.info(f"Problem does not have a solution, since backbone could not be found!")
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

    # 5. done, process and solve!
    # remove any old clingo output files
    remove_files(fond_problem.output_dir, ASP_CLINGO_OUTPUT_PREFIX)

    # set the overall solver model to be used, copy it to output folder
    model_file = f"controller-{fond_problem.controller_model}.lp"
    fond_problem.controller_model = os.path.join(get_package_root(), "asp", model_file)
    shutil.copy(fond_problem.controller_model, fond_problem.output_dir)

    if fond_problem.filter_undo:
        compile_undo_actions(fond_problem, fond_problem.output_dir)

    if fond_problem.domain_knowledge:
        generate_knowledge(
            fond_problem,
            initial_state,
            goal_state,
            nd_actions,
            variables,
            fond_problem.domain_knowledge,
        )

    # time to SOLVE the problem by the iterative process
    if fond_problem.time_limit and USE_ASYNCIO:
        asyncio.run(
            solve_asp_iteratively_async(fond_problem, min_controller_size)
        )
    else:
        solve_asp_iteratively(
            fond_problem, min_states=min_controller_size
        )
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

            # ASP input files for Clingo
            input_files = [fond_problem.controller_model, fond_problem.instance_file]
            if fond_problem.domain_knowledge is not None:
                input_files.append(fond_problem.domain_knowledge)
            if fond_problem.controller_constraints.values() is not None:
                input_files += fond_problem.controller_constraints.values()

            # build executable command
            args = [f"-c numStates={num_states}"] + fond_problem.clingo_args
            cmd_executable = [fond_problem.clingo] + input_files + args

            # cmd_executable = ["echo", "Hello, world!"]
            # print(cmd_executable)

            # write start info on the output file for this run
            asp_output_file = os.path.join(
                fond_problem.output_dir, f"{ASP_CLINGO_OUTPUT_PREFIX}{num_states}.out"
            )
            file_out = open(asp_output_file, "a")
            file_out.write(f"Time start: {get_now()}\n\n")
            file_out.write(' '.join(cmd_executable))
            file_out.write("\n")

            # now do the async run with a time limit
            return_code, stdout = await run_subprocess(cmd_executable, time_left)

            # save the ASP run output to the ouput file (already opened above)
            file_out.write(stdout)
            file_out.write("\n\n")
            file_out.write(f"Time end: {get_now()}\n")
            file_out.write(f"Clingo return code: {return_code}\n")
            file_out.close()

            if stdout is None:
                _logger.warning(f"No output on ASP run with {num_states} controller states?")
                continue
            if "SATISFIABLE" in stdout and "UNSATISFIABLE" not in stdout:
                return True # yes, found solution!

            # not a solution yet, keep looping with more controller states
            # if < 0, just set a minimal timeout for the next cycle
            time_left -= time.time() - start_time
            if time_left <= 0:
                time_left = 0.1

    # main process
    try:
        await asyncio.wait_for(run_with_time_limit(), timeout=time_limit)
    except asyncio.TimeoutError:
        print("Overall timeout reached before completing all runs.")


async def run_subprocess(args, time_left):
    """Runs an external program using asyncio.
        Integrate stderr into stdout

        return both process return code and stdout
    """

    _logger: logging.Logger = _get_logger()

    # run clingo in a separate process
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    stdout, _ = await asyncio.wait_for(process.communicate(), time_left)
    stdout = stdout.decode().strip()

    return process.returncode, stdout


def solve_asp_iteratively(fond_problem, min_states):
    """Runs the function `n` times with an overall timeout of `timeout` seconds."""
    _logger: logging.Logger = _get_logger()

    # a local function to run the function with a time limit
    def run_with_time_limit():
        time_left = float("inf")    # default
        if fond_problem.time_limit is not None:
            time_left = fond_problem.time_limit
        for num_states in range(
            min_states, fond_problem.max_states + 1, fond_problem.inc_states
        ):
            start_time = time.time()
            _logger.info(f"Solving with number of controller states={num_states} - Time left: {time_left:.2f}")

            # ASP input files for Clingo
            input_files = [fond_problem.controller_model, fond_problem.instance_file]
            if fond_problem.domain_knowledge is not None:
                input_files.append(fond_problem.domain_knowledge)
            if fond_problem.controller_constraints.values() is not None:
                input_files += fond_problem.controller_constraints.values()

            # build executable command
            args = [f"-c numStates={num_states}"] + fond_problem.clingo_args
            cmd_executable = [fond_problem.clingo] + input_files + args

            # cmd_executable = ["echo", "Hello, world!"]
            # print(cmd_executable)

            # write start info on the output file for this run
            asp_output_file = os.path.join(
                fond_problem.output_dir, f"{ASP_CLINGO_OUTPUT_PREFIX}{num_states}.out"
            )
            file_out = open(asp_output_file, "a")
            file_out.write(f"Time start: {get_now()}\n\n")
            file_out.write(" ".join(cmd_executable))
            file_out.write("\n")

            # now do the async run with a time limit
            process = subprocess.run(
                cmd_executable,
                cwd=fond_problem.output_dir,
                # capture_output=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=time_left if time_left < float("inf") else None,
            )
            return_code = process.returncode
            stdout = process.stdout.decode()

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
                return True  # yes, found solution!

            # not a solution yet, keep looping with more controller states
            # if < 0, just set a minimal timeout for the next cycle
            time_left -= time.time() - start_time
            if time_left <= 0:
                time_left = 0.1

        return False # have tried all sizes and no solution found!

    # main process
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


def generate_asp_instance_inc(file, initial_state, goal_state, variables, mutexs, nd_actions, initial_state_encoding="both", action_var_affects=False):
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


def generate_asp_instance(file, initial_state, goal_state, variables, mutexs, nd_actions, initial_state_encoding="both", action_var_affects=False):
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


def parse_and_translate(fond_problem: FONDProblem) -> (State, State, dict[str: Action], dict[str: List[Action]], list[Variable], list[State]):
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


def compile_undo_actions(fond_problem: FONDProblem, output_dir: str):
    undo_controller = fond_problem.controller_constraints["undo"]
    instance_file = os.path.join(output_dir, "instance.lp")
    output_file = os.path.join(output_dir, "undo_actions.out")
    executable_list = [fond_problem.clingo, instance_file, undo_controller, "--stats"]

    process = subprocess.Popen(executable_list, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    stdout, stderr = process.communicate()

    # save output
    with open(output_file, "w") as f:
        f.write(stdout.decode())

    # create grounded file
    grounded_undo_file = os.path.join(output_dir, "undo_actions.lp")
    write_undo_actions(output_file, grounded_undo_file, process_action_type=fond_problem.filter_undo)

    # replace the undo constraint with the precompiled one
    fond_problem.controller_constraints["undo"] = grounded_undo_file


def generate_knowledge(fond_problem, initial_state, goal_state, nd_actions, variables, domain_knowledge):
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
    coloredlogs.install(level=DEBUG_LEVEL)
    return logger

logger = _get_logger()
