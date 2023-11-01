import asyncio
import logging
import subprocess
from typing import List, Tuple, Dict, Any
import coloredlogs
from async_timeout import timeout
from base.config import ASP_CLINGO_OUTPUT_PREFIX
from base.elements import FONDProblem, Action, Variable, State
from utils.backbone import get_backbone_asp, create_backbone_constraint
from utils.fd import compute_weak_plan
from utils.helper_asp import write_variables, write_mutex, write_goal_state, write_actions, write_initial_state, write_undo_actions
from utils.helper_clingo import execute_asp, execute_asp_async
from utils.helper_sas import organize_actions
from utils.translators import determinise, parse_sas
from knowledge.blocksworld import BlocksworldKnowledge
from knowledge.tireworld import TireworldKnowledge
from knowledge.miner import MinerKnowledge
from knowledge.acrobatics import AcrobaticsKnowledge
from knowledge.spiky import SpikyTireworldKnowledge
import os


def solve_with_backbone(fond_problem: FONDProblem, output_dir: str, only_size=False):
    """
    First we generate a backbone using classical planner and then use that to constrain the controller.
    :param fond_problem: FOND problem
    :param output_dir:
    :param only_size: If True, only the size of the backbone is considered as a lower bound to the controller
    :return:
    """
    _logger: logging.Logger = _get_logger()
    _logger.info(f"Solving {fond_problem.domain} with problem {fond_problem.problem} using backbone.")

    # determinise, translate to SAS and parse the SAS file
    initial_state, goal_state, det_actions, nd_actions, variables, mutexs = parse(fond_problem, output_dir)

    # generate ASP instance
    file: str = f"{output_dir}/instance.lp"
    generate_asp_instance(file, initial_state, goal_state, variables, mutexs, nd_actions)
   
    classical_planner = fond_problem.classical_planner
    clingo_inputs = [classical_planner, file]
    args = ["--stats"]
    out_file = f"{output_dir}/weak_plan.out"
    if fond_problem.seq_kb:
        clingo_inputs.append(fond_problem.seq_kb)
    execute_asp(fond_problem.clingo, args, clingo_inputs, output_dir, out_file)

    # get the backbone
    backbone: List[tuple[str, str]] = get_backbone_asp(out_file)
    min_controller_size = len(backbone)
  
    if min_controller_size == 0:
        # problem is unsatisfiable
        _logger.info(f"Problem does not have a solution, since backbone could not be found!")
        with open (f"{output_dir}/unsat.out", "w+") as f:
            f.write("Unsat")
        return
    
    _logger.info(f"Backbone is of size {min_controller_size}.")

    if not only_size:
        constraint_file = f"{output_dir}/backbone.lp"
        create_backbone_constraint(backbone, constraint_file)
        fond_problem.controller_constraints["backbone"] = constraint_file

    preprocess_and_solve(fond_problem, output_dir, initial_state, goal_state, nd_actions, variables, file, min_controller_size)


def solve(fond_problem: FONDProblem, output_dir: str):
    _logger: logging.Logger = _get_logger()
    _logger.info(f"Solving {fond_problem.domain} with problem {fond_problem.problem} using ASP.")

    # determinise, translate to SAS and parse the SAS file
    initial_state, goal_state, det_actions, nd_actions, variables, mutexs = parse(fond_problem, output_dir)

    file: str = f"{output_dir}/instance.lp"
    generate_asp_instance(file, initial_state, goal_state, variables, mutexs, nd_actions, initial_state_encoding="both", action_var_affects=False)
    preprocess_and_solve(fond_problem, output_dir, initial_state, goal_state, nd_actions, variables, file)


def set_model(nd_actions, fond_problem: FONDProblem):
    """
    If the maximum degree of non determinism is only 2 then we can solve it slightly more efficiently.
    """
    match(fond_problem.controller_model):
        case "fondsat":
            name = "fondsat"
        case "regression":
            name = "reg"

    max_nd = 0
    for _, actions_list in nd_actions.items():
        if len(actions_list) > max_nd:
            max_nd = len(actions_list)

    suffix = ""
    if max_nd > 2:
        suffix = "-gen"

    controller = f"controller-{name}{suffix}.lp"
    fond_problem.controller_model = os.path.join(fond_problem.root, "asp", controller)
        

def preprocess_and_solve(fond_problem, output_dir, initial_state, goal_state, nd_actions, variables, file, min_controller_size=1):
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
    async with timeout(fond_problem.time_limit):
        try:
            # check if a solution exists with the given minimum states
            solution_found = await _run_clingo_async(fond_problem, instance, min_states, output_dir)
            if solution_found:
                direction = -1
            else:
                direction = 1

            num_states = min_states + direction

            while 0 < num_states <= fond_problem.max_states and not stop:
                solution_found = await _run_clingo_async(fond_problem, instance, num_states, output_dir)

                # check if a solution was found or the process timed out
                if solution_found and direction == 1:
                    _logger.info(f"Solution found!")
                    stop = True

                elif not solution_found and direction == -1:
                    _logger.info(f"Solution found!")
                    stop = True

                num_states += direction
        except asyncio.CancelledError:
            _logger.info(f"Timed Out with numStates={num_states}.")
            out_file = f"{output_dir}/{ASP_CLINGO_OUTPUT_PREFIX}{num_states}.out"
            with open(out_file, "w") as f:
                f.write(f"TimedOut.")


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
        direction = -1
    else:
        direction = 1

    num_states = min_states + direction

    while 0 < num_states <= fond_problem.max_states and not stop:
        solution_found = _run_clingo(fond_problem, instance, num_states, output_dir)

        # check if a solution was found or the process timed out
        if solution_found and direction == 1:
            _logger.info(f"Solution found for id {fond_problem.domain}, {fond_problem.problem}!")
            stop = True

        elif not solution_found and direction == -1:
            _logger.info(f"Solution found for id {fond_problem.id}!")
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
    out_file = f"{output_dir}/{ASP_CLINGO_OUTPUT_PREFIX}{num_states}.out"
    args = [f"-c numStates={num_states}"] + fond_problem.clingo_args

    controller = fond_problem.controller_model
    kb = fond_problem.domain_knowledge
    constraints = fond_problem.controller_constraints.values()

    # input files for clingo
    input_files = [controller, instance]
    if kb is not None:
        input_files.append(kb)
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
    out_file = f"{output_dir}/{ASP_CLINGO_OUTPUT_PREFIX}{num_states}.out"
    args = [f"-c numStates={num_states}"] + fond_problem.clingo_args

    controller = fond_problem.controller_model
    kb = fond_problem.extra_kb
    constraints = fond_problem.controller_constraints.values()

    # input files for clingo
    input_files = [controller, instance]
    if kb is not None:
        input_files.append(kb)
    if constraints is not None:
        input_files += constraints

    # run clingo in a separate process
    solution_found = execute_asp(fond_problem.clingo, args, input_files, output_dir, out_file)

    return solution_found


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
    sas_stats_file = f"{output_dir}/sas_stats.txt"
    sas_file = f"{output_dir}/output.sas"

    # determinise!
    determinise(fond_problem, output_dir, sas_stats_file)

    initial_state, goal_state, actions, variables, mutexs = parse_sas(sas_file)
    det_actions, nd_actions = organize_actions(actions)

    return initial_state, goal_state, det_actions, nd_actions, variables, mutexs


def compile_undo_actions(fond_problem: FONDProblem, output_dir: str):
    undo_controller = fond_problem.controller_constraints["undo"]
    instance_file = f"{output_dir}/instance.lp"
    output_file = f"{output_dir}/undo_actions.out"
    executable_list = [fond_problem.clingo, instance_file, undo_controller, "--stats"]

    process = subprocess.Popen(executable_list, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    stdout, stderr = process.communicate()

    # save output
    with open(output_file, "w") as f:
        f.write(stdout.decode())

    # create grounded file
    grounded_undo_file = f"{output_dir}/undo_actions.lp"
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
