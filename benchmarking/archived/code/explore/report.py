"""
Generate csv from the output
"""
import logging
import os
import re

import coloredlogs

output_folder = "./output/"
re_clingo_time = r"(?P<total>[\d.]+)s \(Solving: (?P<solving>[\d.]+)s 1st Model: (?P<sat>[\d.]+)s Unsat: (?P<unsat>[\d.]+)s"
re_clingo = r"clingo_out_(?P<states>[\d]+).out"

final_stats = [f"domain,instance,configuration,sat_time,unsat_time,states{os.linesep}"]
interim_stats = [f"domain,instance,configuration,time,choices,conflicts,restarts,constraints,variables,sat,iteration{os.linesep}"]


def parse_file(file):
    data = {}
    with open(file) as r:
        info = r.readlines()
        for l in info:
            if "CPU Time" in l:
                _s = l.split(":")[-1].strip().replace("s","")
                data["cpu_time"] = float(_s)
            if "Time" in l and "CPU" not in l:
                _s = ":".join(l.split(":")[1:]).strip()
                result = re.match(re_clingo_time, _s)
                sat_time = float(result.group("sat"))
                unsat_time = float(result.group("unsat"))
                data["sat"] = sat_time
                data["unsat"] = unsat_time
                data["total_time"] = float(result.group("total"))
            elif "Choices" in l:
                _s = l.split(":")[-1].strip()
                data["choices"] = int(_s)
            elif "Conflicts" in l:
                _tokens = l.split(":")[1].strip()
                _s = _tokens.split(" ")[0].strip()
                data["conflicts"] = int(_s)
            elif "Restarts" in l:
                _tokens = l.split(":")[1].strip()
                _s = _tokens.split(" ")[0].strip()
                data["restarts"] = int(_s)
            elif "Variables" in l:
                _tokens = l.split(":")[1].strip()
                _s = _tokens.split(" ")[0].strip()
                data["variables"] = int(_s)
            elif "Constraints" in l:
                _tokens = l.split(":")[1].strip()
                _s = _tokens.split(" ")[0].strip()
                data["constraints"] = int(_s)

    return data


def get_run_time_stats(clingo_folder):
    files = [f for f in os.scandir(clingo_folder) if f.name.startswith("clingo")]
    sat_time = 0
    unsat_time = 0
    states = 0
    for f in files:
        result = re.match(re_clingo, f.name)
        iteration = int(result.group("states"))

        if iteration > states:
            states = iteration

        info = parse_file(f"{clingo_folder}/{f.name}")

        sat_time += info["sat"]
        unsat_time += info["unsat"]

    return {"sat_time": sat_time, "unsat_time": unsat_time, "states": states}


def get_final_stats(d, instance, configuration, clingo_folder):
    global final_stats
    stats = get_run_time_stats(clingo_folder)
    final_stats.append(f"{d},{instance},{configuration},{stats['sat_time']},{stats['unsat_time']},{stats['states']}{os.linesep}")


def get_interim_stats(d, i, c, clingo_folder):
    # interim_stats = [f"domain,instance,configuration,time,choices,conflicts,restarts,constraints,variables,sat,iteration{os.linesep}"]
    global interim_stats
    files = [f for f in os.scandir(clingo_folder) if f.name.startswith("clingo")]
    for f in files:
        result = re.match(re_clingo, f.name)
        iteration = int(result.group("states"))
        info = parse_file(f"{clingo_folder}/{f.name}")
        if info['sat'] > info['unsat']:
            solve_time = info['sat']
            sat = 1
        else:
            solve_time = info['unsat']
            sat = 0

        row = f"{d},{i},{c},{solve_time},{info['choices']},{info['conflicts']},{info['restarts']},{info['constraints']},{info['variables']},{sat},{iteration}{os.linesep}"
        interim_stats.append(row)


def process_stats(d, instance, configuration, clingo_folder):
    get_final_stats(d, instance, configuration, clingo_folder)
    get_interim_stats(d, instance, configuration, clingo_folder)


def run():
    domains = [f for f in os.listdir(output_folder) if os.path.isdir(f"{output_folder}/{f}")]
    for d in domains:
        domain_folder = f"{output_folder}/{d}"
        instances = [i for i in os.listdir(domain_folder) if os.path.isdir(f"{domain_folder}/{i}")]
        for instance in instances:
            instance_folder = f"{domain_folder}/{instance}"
            configurations = [c for c in os.listdir(instance_folder) if os.path.isdir(f"{instance_folder}/{c}")]
            for configuration in configurations:
                clingo_folder = f"{instance_folder}/{configuration}"
                process_stats(d, instance, configuration, clingo_folder)

    with open(f"{output_folder}/final.csv", "w") as f:
        f.writelines(final_stats)

    with open(f"{output_folder}/interim.csv", "w") as f:
        f.writelines(interim_stats)


if __name__ == "__main__":
    logger = logging.getLogger("Explorer")
    coloredlogs.install(level='DEBUG')
    run()
