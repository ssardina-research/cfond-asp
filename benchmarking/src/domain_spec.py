import os
import re

REPORT_FILE = "report.csv"
REPORT_HEADER = ["SAT", "time", "memory", "timeout", "memoryout", "policysize"]

###############################################
# PRIVATE
###############################################
re_file_name = r"clingo_out_(?P<idx>[\d]+).out"
ASP_CLINGO_OUTPUT_PREFIX = "clingo_out_"
NA = "-1"
OUTPUT = []

def _get_file_id(f: str) -> int:
    result = re.match(re_file_name, f)
    idx = int(result.group("idx"))
    return idx


def _get_last_output_file(output_dir) -> str:
    files = os.listdir(output_dir)
    clingo_output_files = [f for f in files if ASP_CLINGO_OUTPUT_PREFIX in f]
    ids = [_get_file_id(f) for f in clingo_output_files]
    if len(ids) == 0:
        return NA, NA
    last_id = ids.index(max(ids))

    return clingo_output_files[last_id], ids[last_id]


def _get_memory(file: str):
    memory_used = NA
    memory_exceeded = NA
    with open(file) as _h:
        data = _h.readlines()

    for _l in data:
        if "used" in _l:
            memory_used = _l.split(":")[1].strip()
        elif "exceeded" in _l:
            if "false" in _l.split(":")[1].strip().lower():
                memory_exceeded = 0
            elif "true" in _l.split(":")[1].strip().lower():
                memory_exceeded = 1

    return memory_used, memory_exceeded

def _is_timed_out(folder: str):
    _file, _ = _get_last_output_file(folder)
    with open(os.path.join(folder, _file)) as _h:
        data = _h.readlines()

    for _l in data:
        if "timed out" in _l.lower():
            return 1

    return 0


def _get_time(folder: str):
    solve_time = NA
    timed_out = NA

    file_time = os.path.join(folder, "solve_time.out")
    if not os.path.exists(file_time):
        return solve_time, timed_out

    timed_out = _is_timed_out(folder)

    with open(file_time) as _h:
        data = _h.readlines()

    for _l in data:
        if "Totaltime" in _l:
            solve_time = _l.split(":")[1].strip()

    return solve_time, timed_out



###############################################
# PUBLIC API
###############################################

# do not touch
def get_scenario_instance(instance):
    return instance["scenario"]

# do not touch
def get_id_instance(instance):
    return instance['id']


# -----------------------
# These have to be specified for the domain at hand
# -----------------------
def get_exec_cmd(instance, solver_args, output_path, time_limit, mem_limit):
    PLANNER = "./src/python/main.py"

    domain = instance["domain"]
    problem = instance["problem"]

    if time_limit > 0:
        solver_args = f"--timeout {time_limit} {solver_args}"

    cmd = f"python {PLANNER} {domain} {problem} {solver_args} --output {output_path}"

    return cmd


def is_solved(folder: str):
    """
    Check if the instance was solved given the output folder.
    """
    if not os.path.exists(folder):
        return False
    _file, _ = _get_last_output_file(folder)

    if _file == NA:
        return NA

    with open(os.path.join(folder, _file)) as _handle:
        data = _handle.readlines()

    for _l in data:
        if "UNSATISFIABLE" in _l:
            return False

    return True



def get_report_row(folder: str):
    if not os.path.exists(folder):
        return {}

    file_memory = os.path.join(folder, "memory.out")
    file_unsat = os.path.join(folder, "unsat.out")

    if os.path.isfile(file_unsat):
        sat = "False"
    elif is_solved(folder):
        sat = "True"
    else:
        sat = NA

    time_solve, time_out = _get_time(folder)
    memory_used, memory_exceeded = _get_memory(file_memory)
    _, last_id = _get_last_output_file(folder)

    if last_id != NA:
        policy_size = last_id + 1
    else:
        policy_size = NA

    if time_out or memory_exceeded:
        policy_size = NA

    return [sat, time_solve, time_out, memory_used, memory_exceeded, policy_size]

