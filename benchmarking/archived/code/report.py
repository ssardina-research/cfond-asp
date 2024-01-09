"""
Script to extract results from the output folder.
This is a quick and dirty script.
Assumptions:
1. First level directory is the domain, second level is the instance
2. ASP outputs are prefixed with "asp", fondsat outputs are prefixed with "glucose" and "minisat", PRP outputs are prefixed with "prp" and Paladinus outputs are prefixed with "paladinus".
"""
import logging
import os
import coloredlogs
import re
re_file_name = r"clingo_out_(?P<idx>[\d]+).out"
ASP_CLINGO_OUTPUT_PREFIX = "clingo_out_"

ROOT_FOLDER = os.path.expanduser("~/Work/Data/FondAsp/")
OUTPUT_FOLDER = f"{ROOT_FOLDER}/output"
CSV_FILE = f"{ROOT_FOLDER}/results.csv"
BACKBONE_FILE = f"{ROOT_FOLDER}/backbone.csv"

INSTANCES = {}
PLANNERS = {"asp1-4h": "asp", "asp2-backbone-4h": "asp", "asp2-4h-kb2": "asp", "asp2-4h-undo": "asp", "asp2-reg-4h": "asp", "asp2-reg-kb-4h": "asp", "asp2-reg-undo-4h": "asp", "asp1-reg-4h": "asp",
            "glucose-4h": "fondsat", "minisat-4h": "fondsat", "paladinus-4h": "paladinus", "prp-4h": "prp"}


HEADERS = ["domain","instance","planner","type","solved","SAT","time","memory","timeout","memoryout","policysize"]
OUTPUT = []

HEADERS_BACKBONE = ["domain", "instance", "backbonesize", "time"]
BACKBONE_OUTPUT = []

TIME_LIMIT = 14400 - 10
MEMORY_LIMIT = 4096
MEMORY_PALADINUS = 3074
NA = "-1"

def get_prp_policy_size(policy_path: str):
    with open(policy_path) as f:
        data = f.readlines()

    count = 0
    for l in data:
        if "Execute:" in l:
            count += 1

    return count + 1 # because we count states whereas they report actions

def parse_fondsat(loc: str, instance_name: str):
    file_path = f"{loc}/{instance_name}.out"

    if not os.path.isfile(file_path):
        return 
    
    with open(file_path) as f:
        data = f.readlines()

    solved = False
    sat = NA
    time_out = False
    memory_out = False
    policy_size = NA
    relevant_info = data[-25:]
    done = False
    for l in relevant_info:
        if "Solved with" in l:
            solved = True
            sat = True
            policy_size = l.split(" ")[2].strip()
        elif "Trying with 101 states" in l:
            solved = False
            sat = NA
        elif "Total time(sec)" in l:
            time = float(l.split(":")[1].strip())
            if time > TIME_LIMIT:
                time_out = True
        elif "Peak memory(MB)" in l:
            memory = float(l.split(":")[1].strip())
            if memory > MEMORY_LIMIT:
                memory_out = True
        elif "done" == l.strip().lower():
            done = True

    if not done:
        time_out = True
    
    return {"solved": solved, "sat": sat, "time": time, "memory": memory, "timeout": time_out, "memoryout": memory_out, "policysize": policy_size}

def parse_prp(loc: str, instance_name: str):
    file_path = f"{loc}/{instance_name}.out"
    
    if not os.path.isfile(file_path):
        return 
    with open(file_path) as f:
        data = f.readlines()

    solved = False
    sat = NA
    time_out = False
    memory_out = False
    policy_size = NA
    relevant_info = data[-25:]
    for l in relevant_info:
        if "plan found" in l.lower():
            solved = True
            sat = True
        elif "No solution" in l:
            solved = True
            sat = False
        elif "Total time(sec)" in l:
            time = float(l.split(":")[1].strip())
            if time > TIME_LIMIT:
                time_out = True
        elif "Peak memory(MB)" in l:
            memory = float(l.split(":")[1].strip())
            if memory > MEMORY_LIMIT:
                memory_out = True
        elif "Memory limit has been reached" in l:
            memory_out = True
            solved = False

    if solved and sat:
        policy_size = get_prp_policy_size(f"{loc}/policy.out")

    return {"solved": solved, "sat": sat, "time": time, "memory": memory, "timeout": time_out, "memoryout": memory_out, "policysize": policy_size}

def _get_last_output_file(output_dir) -> str:
    files = os.listdir(output_dir)
    clingo_output_files = [f for f in files if ASP_CLINGO_OUTPUT_PREFIX in f]
    ids = [_get_file_id(f) for f in clingo_output_files]
    if len(ids) == 0:
        return NA, NA
    last_id = ids.index(max(ids))
    return clingo_output_files[last_id], ids[last_id]

def _get_file_id(f: str) -> int:
    result = re.match(re_file_name, f)
    idx = int(result.group("idx"))
    return idx

def parse_backbone(loc: str):
    file_path = f"{loc}/weak_plan.out"
    if not os.path.isfile(file_path):
        return {"backbonesize": NA, "time": NA}
    
    with open(file_path)as f:
        data = f.readlines()

    backbone_size = NA
    time = NA
    for l in data:
        if "Calls" in l:
            backbone_size = l.split(":")[1].strip()
        elif "Time" in l:
            time = l.split(":")[1].replace("s", "").strip()

    return {"backbonesize": backbone_size, "time": time}

def parse_asp(loc: str, instance_name: str):
    file_path = f"{loc}/{instance_name}.out"
    unsat_file = f"{loc}/unsat.out"

    if not os.path.isfile(file_path):
        return 

    with open(file_path) as f:
        data = f.readlines()

    solved = False
    sat = NA
    time_out = False
    memory_out = False
    policy_size = NA
    for l in data:
        if "Total time(sec)" in l:
            time = float(l.split(":")[1].strip())
            if time > TIME_LIMIT:
                time_out = True
        elif "Peak memory(MB)" in l:
            memory = float(l.split(":")[1].strip())
            if memory > MEMORY_LIMIT:
                memory_out = True

    if os.path.isfile(unsat_file):
        solved = True
        sat = False
    else:
        out_file, states = _get_last_output_file(loc) 
        policy_size = int(states) + 1 # we start from state 0
        if policy_size > 100 or policy_size == 0:
            solved = False
            time_diff = abs(TIME_LIMIT - time)/TIME_LIMIT
            mem_diff = abs(memory - MEMORY_LIMIT)/MEMORY_LIMIT
            if time_diff < 0.05:
                time_out = True
            elif mem_diff < 0.05:
                memory_out = True
            elif out_file == "-1":
                memory_out = True
            if not time_out and not memory_out:
                print("check!")
        else:
            with open(f"{loc}/{out_file}") as f:
                out_data = f.readlines()

            for _i in out_data:
                if "Answer" in _i.strip():
                    solved = True
                    time_out = False
                    memory_out = False
                    solved = True
                    sat = True

    return {"solved": solved, "sat": sat, "time": time, "memory": memory, "timeout": time_out, "memoryout": memory_out, "policysize": policy_size}

def parse_paladinus(loc: str, instance_name: str):
    file_path = f"{loc}/{instance_name}.out"

    with open(file_path) as f:
        data = f.readlines()

    solved = False
    sat = NA
    time_out = False
    memory_out = False
    policy_size = NA
    relevant_info = data[-25:]
    for l in relevant_info:
        if "Policy successfully found" in l:
            solved = True
            sat = True
        elif "No policy could be found." in l:
            solved = True
            sat = False
        elif "Total time(sec)" in l:
            time = float(l.split(":")[1].strip())
            if time > TIME_LIMIT:
                time_out = True
        elif "Policy Size" in l:
            policy_size = int(l.split("=")[1].strip())+ 1
        elif "Peak memory(MB)" in l:
            memory = float(l.split(":")[1].strip())
            if memory > MEMORY_PALADINUS:
                memory_out = True

    for l in relevant_info: # this is corner case
        if "No policy found due to time-out." in l:
            time_out = True
    if solved:
        time_out = False
        memory_out = False

    return {"solved": solved, "sat": sat, "time": time, "memory": memory, "timeout": time_out, "memoryout": memory_out, "policysize": policy_size}

def process():
    global OUTPUT, BACKBONE_OUTPUT

    domains = [f for f in os.listdir(OUTPUT_FOLDER) if os.path.isdir(f"{OUTPUT_FOLDER}/{f}")]
    logger.info(f"Found {len(domains)} domains.")

    OUTPUT.append(f'{",".join(HEADERS)}{os.linesep}')
    BACKBONE_OUTPUT.append(f'{",".join(HEADERS_BACKBONE)}{os.linesep}')

    for d in domains:
        domain_path = f"{OUTPUT_FOLDER}/{d}"
        instances = [f for f in os.listdir(domain_path) if os.path.isdir(f"{domain_path}/{f}")]
        logger.info(f"Found {len(instances)} domain {d}.")

        for i in instances:
            instance_path = f"{domain_path}/{i}"
            planners = [f for f in os.listdir(instance_path) if os.path.isdir(f"{instance_path}/{f}") if f in PLANNERS]
            logger.info(f"Found {len(planners)} planners for instance {i} of domain {d}.")

            for p in planners:
                planner_type = PLANNERS[p]
                loc = f"{instance_path}/{p}"
                backbone_result, result = None, None

                if planner_type == "asp":
                    result = parse_asp(loc, i)
                    if "backbone" in p:
                        backbone_result = parse_backbone(loc)
                elif planner_type == "fondsat":
                    result = parse_fondsat(loc, i)
                elif planner_type == "paladinus": # check for unsat
                    result = parse_paladinus(f"{instance_path}/{p}", i)
                elif planner_type == "prp": # check for unsat
                    result = parse_prp(loc, i)

                if result:
                    # HEADERS = ["domain","instance","planner","type","solved","SAT","time","memory","timeout","memoryout","policysize"]
                    row = f"{d},{i},{p},{planner_type},{result['solved']},{result['sat']},{result['time']},{result['memory']},{result['timeout']},{result['memoryout']},{result['policysize']}{os.linesep}"
                    OUTPUT.append(row)
                if backbone_result:
                    # HEADERS_BACKBONE = ["domain", "instance", "backbonesize", "time"]
                    row_b = f"{d},{i},{backbone_result['backbonesize']},{backbone_result['time']}{os.linesep}"
                    BACKBONE_OUTPUT.append(row_b)

    with open(CSV_FILE, "w+") as f:
        f.writelines(OUTPUT)
    
    with open(BACKBONE_FILE, "w+") as f:
        f.writelines(BACKBONE_OUTPUT)

if __name__ == "__main__":
    logger = logging.getLogger(f"PlanningBenchmarks")
    coloredlogs.install(level='DEBUG')
    process()

