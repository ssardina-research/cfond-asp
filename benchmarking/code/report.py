import argparse
import logging
import os
import coloredlogs
import re
re_file_name = r"clingo_out_(?P<idx>[\d]+).out"
ASP_CLINGO_OUTPUT_PREFIX = "clingo_out_"
NA = "-1"
OUTPUT = []

REPORT_FILE = "report.csv"

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


def is_timed_out(folder: str):
    _file, _ = _get_last_output_file(folder)
    with open (os.path.join(folder,_file)) as _h:
        data = _h.readlines()

    for _l in data:
        if "timedout" in _l.lower():
            return 1

    return 0

def get_time(folder: str):
    solve_time = NA
    timed_out = NA

    file_time = os.path.join(folder, "solve_time.out")
    if not os.path.exists(file_time):
        return solve_time, timed_out

    timed_out = is_timed_out(folder)

    with open(file_time) as _h:
        data = _h.readlines()

    for _l in data:
        if "Totaltime" in _l:
            solve_time = _l.split(":")[1].strip()

    return solve_time, timed_out


def get_memory(file: str):
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


def get_stats(folder: str):
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

    time_solve, time_out = get_time(folder)
    memory_used, memory_exceeded = get_memory(file_memory)
    _, last_id = _get_last_output_file(folder)

    if last_id != NA:
        policy_size = last_id + 1
    else:
        policy_size = NA

    if time_out or memory_exceeded:
        policy_size = NA

    return sat, time_solve, time_out, memory_used, memory_exceeded, policy_size


def report(output_folder):
    """
    The report assumes the folder structure is the same as created by this benchmark: scenario/problem/solver
    """
    HEADERS = ["domain","instance","planner","SAT","time","memory","timeout","memoryout","policysize"]
    output = [f"{','.join(HEADERS)}{os.linesep}"]
    scenarios = [s for s in os.listdir(output_folder) if os.path.isdir(os.path.join(output_folder, s))]
    for s in scenarios:
        _d = os.path.join(output_folder, s)
        problems = [p for p in os.listdir(_d) if os.path.isdir(os.path.join(_d, p))]
        for p in problems:
            _p = os.path.join(os.path.join(output_folder, s, p))
            solvers = [s for s in os.listdir(_p) if os.path.isdir(os.path.join(_p, s))]
            for sol in solvers:
                _path = os.path.join(output_folder, s, p, sol)
                sat, time_solve, time_out, memory_used, memory_exceeded, policy_size = get_stats(_path)

                row = f"{s},{p},{sol},{sat},{time_solve},{memory_used},{time_out},{memory_exceeded},{policy_size}{os.linesep}"
                output.append(row)

    with open(os.path.join(output_folder, REPORT_FILE), "w+") as f:
        f.writelines(output)


if __name__ == "__main__":
    # CLI options
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Benchmarking script to run FOND instances using CFONDASP planner."
    )
    parser.add_argument("output_folder",
        help="Path to root output directory where all solving information has been saved.")

    args = parser.parse_args()

    report(args.output_folder)
    print(f"Done writing the report to: {os.path.join(args.output_folder, REPORT_FILE)}")
