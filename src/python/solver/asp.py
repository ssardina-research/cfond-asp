import asyncio
import logging
import subprocess
from typing import List, Tuple, Dict, Any
import coloredlogs
from async_timeout import timeout
from base.config import ASP_CLINGO_OUTPUT_PREFIX
from base.elements import FONDProblem, Action, Variable, State
from base.logic_operators import entails
from utils.system_utils import remove_files
from utils.backbone import get_backbone_asp, create_backbone_constraint
from utils.helper_asp import write_goal, write_variables, write_mutex, write_goal_state, write_actions, write_initial_state, write_undo_actions
from utils.helper_clingo import execute_asp, execute_asp_async, set_logger
from utils.helper_sas import organize_actions
from utils.translators import determinise, parse_sas
from knowledge.blocksworld import BlocksworldKnowledge
from knowledge.tireworld import TireworldKnowledge
from knowledge.miner import MinerKnowledge
from knowledge.acrobatics import AcrobaticsKnowledge
from knowledge.spiky import SpikyTireworldKnowledge
import os


def solve(fond_problem: FONDProblem, output_dir: str, back_bone=False, only_size=False):
    """
    First we generate a backbone using classical planner and then use that to constrain the controller.
    :param fond_problem: FOND problem
    :param output_dir:
    :param back_bone: Use backbone technique
    :param only_size: Only the size of the backbone is considered as a lower bound to the controller
    :return:
    """
    _logger: logging.Logger = _get_logger()
    _logger.info(f"Solving {fond_problem.domain} with problem {fond_problem.problem} using backbone={back_bone}.")

    # determinise, translate to SAS and parse the SAS file
    initial_state: State = None
    goal_state: State = None
    initial_state, goal_state, det_actions, nd_actions, variables, mutexs = parse(fond_problem, output_dir)

    # check if initial state is the goal state
    if entails(initial_state, goal_state):
        _logger.info("Goal met in the initial state!")
        _logger.info("Solution found!")
        return

    # generate ASP instance
    file: str = os.path.join(output_dir, "instance.lp")
    generate_asp_instance(file, initial_state, goal_state, variables, mutexs, nd_actions, initial_state_encoding="both", action_var_affects=False)

    min_controller_size = fond_problem.min_states
    if back_bone:

        file_weak_plan: str = os.path.join(output_dir, "instance_inc.lp")
        generate_asp_instance_inc(file_weak_plan, initial_state, goal_state, variables, mutexs, nd_actions)

        classical_planner = fond_problem.classical_planner
        clingo_inputs = [classical_planner, file_weak_plan]
        args = ["--stats"]
        out_file = os.path.join(output_dir, "weak_plan.out")
        if fond_problem.seq_kb:
            clingo_inputs.append(fond_problem.seq_kb)
        execute_asp(fond_problem.clingo, args, clingo_inputs, output_dir, out_file)

        # get the backbone
        backbone: List[tuple[str, str]] = get_backbone_asp(out_file)
        backbone_size = len(backbone)

        if backbone_size == 0:
            # problem is unsatisfiable
            _logger.info(f"Problem does not have a solution, since backbone could not be found!")
            with open (os.path.join(output_dir, "unsat.out"), "w+") as f:
                f.write("Unsat")
            return
        else:
            min_controller_size = max(fond_problem.min_states, backbone_size)

        _logger.info(f"Backbone is of size {backbone_size}.")

        if not only_size:
            constraint_file = os.path.join(output_dir, "backbone.lp")
            create_backbone_constraint(backbone, constraint_file)
            fond_problem.controller_constraints["backbone"] = constraint_file


    preprocess_and_solve(fond_problem, output_dir, initial_state, goal_state, nd_actions, variables, file, min_controller_size)

def set_model(nd_actions, fond_problem: FONDProblem):
    """
    If the maximum degree of non determinism is only 2 then we can solve it slightly more efficiently.
    """
    if fond_problem.solution_type == "strong":
            controller = f"controller-strong.lp"
    else:
        match(fond_problem.controller_model):
            case "fondsat":
                name = "fondsat"
            case "regression":
                name = "reg"
        controller = f"controller-{name}.lp"

    fond_problem.controller_model = os.path.join(fond_problem.root, "asp", controller)


def preprocess_and_solve(fond_problem, output_dir, initial_state, goal_state, nd_actions, variables, file, min_controller_size=1):
    # remove any old clingo output files
    remove_files(output_dir, ASP_CLINGO_OUTPUT_PREFIX)

    # set the solver model
    set_model(nd_actions, fond_problem)

    if fond_problem.filter_undo:
        compile_undo_actions(fond_problem, output_dir)

    if fond_problem.domain_knowledge:
        generate_knowledge(fond_problem, initial_state, goal_state, nd_actions, variables, output_dir, fond_problem.domain_knowledge)

    # solve the asp instance with a time limit
    time_limit: int = fond_problem.time_limit
    if time_limit:
        asyncio.run(solve_asp_instance_async(fond_problem, file, output_dir, min_states=min_controller_size))
    else:
        solve_asp_instance(fond_problem, file, output_dir, min_states=min_controller_size)
    return


async def solve_asp_instance_async(fond_problem: FONDProblem, instance: str, output_dir: str, min_states: int = 1):
    """
       Solve FOND instance by incrementing the number of states and looking for a solution.
       :param fond_problem: Fond problem
       :param instance: ASP instance
       :param output_dir: output directory to store clingo output
       :param min_states: Minimum number of controller states
       :return:
       """
    _logger: logging.Logger = _get_logger()
    stop = False
    # if fond_problem.time_limit == None, no timeout is enforced
    async with timeout(fond_problem.time_limit):
        try:
            # check if a solution exists with the given minimum states
            num_states = min_states # time out may occur in the next step, hence we need to initialise the num_states for later reporting
            solution_found = await _run_clingo_async(fond_problem, instance, num_states, output_dir)
            if solution_found:
                # solution found! we can exit (we don't need to compute the smallest size controller for efficiency)
                _logger.info(f"Solution found!")
                _logger.info(f"Number of states in controller: {num_states+1}")
                stop = True
                # direction = -1 * fond_problem.inc_states
            else:
                direction = 1 * fond_problem.inc_states

            num_states = min_states + direction

            while 0 < num_states <= fond_problem.max_states and not stop:
                solution_found = await _run_clingo_async(fond_problem, instance, num_states, output_dir)

                # check if a solution was found or the process timed out
                if solution_found and direction > 0:
                    _logger.info(f"Solution found!")
                    _logger.info(f"Number of states in controller: {num_states+1}")
                    stop = True

                elif not solution_found and direction < 0:
                    _logger.info(f"Solution found!")
                    _logger.info(f"Number of states in controller: {num_states+1}")
                    stop = True

                num_states += direction
        except asyncio.CancelledError:
            _logger.info(f"Timed Out with numStates={num_states}.")
            out_file = os.path.join(output_dir, f"{ASP_CLINGO_OUTPUT_PREFIX}{num_states}.out")
            with open(out_file, "a") as f:
                f.write(f"Timed out with time limit={fond_problem.time_limit}.\n")


def solve_asp_instance(fond_problem: FONDProblem, instance: str, output_dir: str, min_states: int = 1):
    """
    Solve FOND instance by incrementing or decrementing the number of states and looking for a solution.
    To check if we need to increase or decrease the states, one first checks the solution with the given min_states.
    If a solution does not exist one increments, else one decrements.
    :param fond_problem: Fond problem
    :param instance: ASP instance
    :param output_dir: output directory to store clingo output
    :param min_states: Minimum number of controller states
    :return:
    """
    _logger: logging.Logger = _get_logger()
    stop = False

    # check if a solution exists with the given minimum states
    solution_found = _run_clingo(fond_problem, instance, min_states, output_dir)
    if solution_found:
        # solution found! we can exit (we don't need to compute the smallest size controller for efficiency)
        _logger.info(f"Solution found!")
        _logger.info(f"Number of states in controller: {num_states+1}")
        stop = True
        # direction = -1 * fond_problem.inc_states
    else:
        direction = 1 * fond_problem.inc_states

    num_states = min_states + direction

    while 0 < num_states <= fond_problem.max_states and not stop:
        solution_found = _run_clingo(fond_problem, instance, num_states, output_dir)

        # check if a solution was found or the process timed out
        if solution_found and direction > 0:
            _logger.info(f"Solution found for instance ({fond_problem.domain}, {fond_problem.problem})!")
            _logger.info(f"Number of states in controller: {num_states+1}")
            stop = True

        elif not solution_found and direction < 0:
            _logger.info(f"Solution found for instance ({fond_problem.domain}, {fond_problem.problem})!")
            _logger.info(f"Number of states in controller: {num_states+1}")
            stop = True

        num_states += direction


async def _run_clingo_async(fond_problem: FONDProblem, instance, num_states, output_dir):
    """
    Run clingo with the given configuration
    :param fond_problem: FOND Problem
    :param instance: Clingo input for the instance
    :param num_states: number of states for the controller
    :param output_dir: output directory to store the output
    :return:
    """
    _logger: logging.Logger = _get_logger()
    _logger.info(f" -Solving with numStates={num_states}.")
    out_file = os.path.join(output_dir, f"{ASP_CLINGO_OUTPUT_PREFIX}{num_states}.out")
    args = [f"-c numStates={num_states}"] + fond_problem.clingo_args

    controller = fond_problem.controller_model
    kb = fond_problem.domain_knowledge
    constraints = fond_problem.controller_constraints.values()

    # input files for clingo
    input_files = [controller, instance]
    # if kb is not None:
    #     input_files.append(kb)
    if constraints is not None:
        input_files += constraints

    # run clingo in a separate process
    [solution_found] = await asyncio.gather(execute_asp_async(fond_problem.clingo, args, input_files, output_dir, out_file))

    return solution_found


def _run_clingo(fond_problem: FONDProblem, instance, num_states, output_dir):
    """
    Run clingo with the given configuration
    :param fond_problem: FOND Problem
    :param instance: Clingo input for the instance
    :param num_states: number of states for the controller
    :param output_dir: output directory to store the output
    :return:
    """
    _logger: logging.Logger = _get_logger()
    _logger.info(f" -Solving with numStates={num_states}.")
    out_file = os.path.join(output_dir, f"{ASP_CLINGO_OUTPUT_PREFIX}{num_states}.out")
    args = [f"-c numStates={num_states}"] + fond_problem.clingo_args

    controller = fond_problem.controller_model
    kb = fond_problem.extra_kb
    constraints = fond_problem.controller_constraints.values()

    # input files for clingo
    input_files = [controller, instance]
    if constraints is not None:
        input_files += constraints

    # run clingo in a separate process
    solution_found = execute_asp(fond_problem.clingo, args, input_files, output_dir, out_file)

    return solution_found


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


def parse(fond_problem: FONDProblem, output_dir: str) -> (State, State, dict[str: Action], dict[str: List[Action]], list[Variable], list[State]):
    """
    Returns the parsed PDDL Domain, PDDL problem, SAS initial state, SAS goal state, dictionary of deterministic and non-deterministic actions
    :param fond_problem: A Fond problem with the required inputs
    :param output_dir: Path to the output directory
    :param temp_dir: Path to the temporary directory
    :return: Parsed PDDL domain, PDDL problem, SAS initial state, SAS goal state, dictionary of deterministic actions, dictionary of non-deterministic actions
    """
    sas_stats_file = os.path.join(output_dir, "sas_stats.txt")
    sas_file = os.path.join(output_dir, "output.sas")

    # determinise!
    determinise(fond_problem, output_dir, sas_stats_file)

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


def generate_knowledge(fond_problem, initial_state, goal_state, nd_actions, variables, output_dir, domain_knowledge):
    if domain_knowledge.lower() == "triangle-tireworld":
        kb = TireworldKnowledge(fond_problem, variables, output_dir)
        kb.add_knowledge()
    elif domain_knowledge.lower() == "miner":
        kb = MinerKnowledge(fond_problem, variables, output_dir)
        kb.add_knowledge()
    elif domain_knowledge.lower() == "acrobatics":
        kb = AcrobaticsKnowledge(fond_problem, variables, output_dir)
        kb.add_knowledge()
    elif domain_knowledge.lower() == "spikytireworld":
        kb = SpikyTireworldKnowledge(fond_problem, variables, nd_actions, output_dir)
        kb.add_knowledge()


def _get_logger() -> logging.Logger:
    logger = logging.getLogger("FondASP")
    coloredlogs.install(level='INFO')
    return logger

set_logger(_get_logger())
