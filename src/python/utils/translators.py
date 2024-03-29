import os.path

from base.elements import FONDProblem
from utils.helper_sas import *
from utils.helper_sas import get_indices_variables
import subprocess


def determinise(fond_problem: FONDProblem, output_dir, sas_stats_file):
    """
    Determinise using FD translator
    :param fond_problem:
    :param output_dir:
    :param sas_stats_file:
    :return:
    """
    translator: str = fond_problem.sas_translator
    sas_file = f"{output_dir}/output.sas"
    execute_translator(translator, fond_problem.domain, fond_problem.problem, fond_problem.translator_args, output_dir, sas_file, sas_stats_file)


def parse_sas(sas_file: str) -> (State, State, tuple[list[Action], list[Variable]], List[State]):
    """
    Returns the initial state, goal state, and list of actions from a SAS file.
    :param sas_file: path to the sas file
    :return: Initial state, Goal state, List of actions
    """
    with open(sas_file) as f:
        info = f.readlines()

    # extract variables
    variable_indices: List[tuple[int, int]] = get_indices_variables(info)
    variables: List[Variable] = []
    for (i, j) in variable_indices:
        var = get_variable(info[i+1: j])
        variables.append(var)

    # extract actions
    action_indices: List[tuple[int, int]] = get_indices_operators(info)
    actions: List[Action] = []
    for (i, j) in action_indices:
        action = get_action(info[i+1: j], variables)
        action.generate_strips()
        actions.append(action)

    # initial state
    init_i, init_j = get_indices_initial_state(info)
    initial_state: State = State(variables, [-1] * len(variables))
    for i in range(init_i + 1, init_j):
        var_idx: int = i - (init_i + 1)
        val = int(info[i])
        initial_state.values[var_idx] = val

    # goal state
    init_i, init_j = get_indices_goal(info)
    goal_state: State = State(variables, [-1] * len(variables))
    num_vars = int(info[init_i + 1])
    for i in range(init_i + 2, init_j):
        [var_idx, val] = map(int, info[i].split())
        goal_state.values[var_idx] = val

    # mutex, we can model a mutex as a partial state. It represents a state that will never occur in the planning problem.
    mutex_indices: List[tuple[int, int]] = get_indices_mutex(info)
    mutexs: List[State] = []
    for (i, j) in mutex_indices:
        mutex: State = State(variables, [-1] * len(variables))
        for k in range(i+2, j):
            [var_idx, val] = map(int, info[k].split())
            mutex.values[var_idx] = val
        mutexs.append(mutex)

    return initial_state, goal_state, actions, variables, mutexs


def execute_translator(translate_path: str, domain: str, problem: str, translator_args: str, output_dir: str, sas_file: str, stats_file: str):
    """
    Execute the prp translator on the given domain and problem to generate a SAS output.
    :param translate_path: path to prp translate
    :param domain: path to the domain file
    :param problem: path to the problem file
    :param translator_args: A template of arguments to pass to the translator
    :param output_dir: path to the output directory where output.sas will be saved
    :param stats_file: path to the stats file where the translation stats will be saved
    :return:
    """

    translator_cmd = translator_args.replace("{domain}", domain).replace("{instance}", problem).replace("{sas_file}", sas_file)
    execution_cmd = ["python", translate_path] + translator_cmd.split()
    process = subprocess.Popen(execution_cmd, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    # save output
    with open(stats_file, "w") as f:
        f.write(stdout.decode())


if __name__ == "__main__":
    # parse the pddl file
    domain_file: str = os.path.expanduser("~/Work/Software/PyPRP/examples/blocksworld/domain_det.pddl")
    problem_file: str = os.path.expanduser("~/Work/Software/PyPRP/examples/blocksworld/p01.pddl")
    output: str = "./output/temp/"
    stats_file: str = os.path.expanduser("~/Work/Software/PyPRP/output/temp/translator_stats.txt")
    # domain: Domain = PDDLParser.parse("./examples/blocksworld/domain01.pddl")
    # _domain = get_deterministic_domain(domain)
    # problem: Problem = PDDLParser.parse("./examples/blocksworld/p01.pddl")
    #
    # with open("./examples/blocksworld/domain_det.pddl", "w") as f:
    #     f.writelines(repr(_domain))
    # i, g, actions = parse_sas("./output/output.sas")
    # organize_actions(actions)
