import logging
import os
import coloredlogs
import re
re_file_name = r"clingo_out_(?P<idx>[\d]+).out"
ASP_CLINGO_OUTPUT_PREFIX = "clingo_out_"
HEADERS = ["domain","instance","planner","solved","SAT","time","memory","timeout","memoryout","policysize"]
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

def is_solved(folder: str):
    """
    Check if the instance was solved given the output folder.
    """
    if not os.path.exists(folder):
        return False
    _file, _ = _get_last_output_file(folder)
    with open(os.path.join(folder, _file)) as _handle:
        data = _handle.readlines()

    for _l in data:
        if "UNSATISFIABLE" in _l:
            return False
        
    return True


def is_timed_out(folder: str):
    _file, _ = _get_last_output_file(folder)
    with open (_file) as _h:
        data = _h.readlines()
    
    for _l in data:
        if "timedout" in _l.lower():
            return True
        
def is_memory_out(file: str):
    with open(file) as _h:
        data = _h.readlines()

    
 
def get_stats(folder: str):
    if not os.path.exists(folder):
        return {}

    file_time = os.path.join(folder, "solve_time.out")
    file_memory = os.path.join(folder, "memory.out")
    file_unsat = os.path.join(folder, "unsat.out")

    if os.path.isfile(file_unsat):
        sat = "False"
    elif is_solved(folder):
        sat = "True"
    else:
        sat = NA

    _time_out = is_timed_out(folder)