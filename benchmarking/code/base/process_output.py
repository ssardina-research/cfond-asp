import argparse
import logging
import os
import re
import sys

import coloredlogs

re_clingo = r"clingo_out_(?P<states>[\d]+).out"
re_clingo_time = r"(?P<total>[\d.]+)s \(Solving: (?P<solving>[\d.]+)s"
re_sat = r"Solved with (?P<states>[\d]+) states"
re_sat_time = r"(?P<time>[\d.]+)"
re_sat_iteration = r"Trying with (?P<iteration>[\d]+) states"


def get_args():
    args_parser = argparse.ArgumentParser(description='Output processor')
    args_parser.add_argument('output_path', help='Path to folder containing output from the solvers.')
    args_parser.add_argument('csv_dir', help='Directory where the csvs should be saved.')
    args_parser.add_argument('-s', '--scenario', help="Process only the given scenario.")

    return vars(args_parser.parse_args())


def get_interim_asp_info(path):
    data = {}
    files = [f for f in os.listdir(path) if f.endswith("out") and f.startswith("clingo")]
    for f in files:
        result = re.match(re_clingo, f)
        iteration = int(result.group("states")) - 1
        data[iteration] = {}

        with open(f"{path}/{f}") as r:
            info = r.readlines()
            for l in info:
                if "Time" in l and "CPU" not in l and "timedout" not in l.lower():
                    _s = ":".join(l.split(":")[1:]).strip()
                    result = re.match(re_clingo_time, _s)
                    total = float(result.group("total"))
                    solve = float(result.group("solving"))
                    ground = total - solve
                    data[iteration]["total"] = total
                    data[iteration]["solve"] = solve
                    data[iteration]["ground"] = ground

    return data


def _extract_times(l):
    data = []
    _t = l.split(":")[1]
    tokens = _t.split(",")
    for t in tokens:
        _i = t.replace("[", "").replace("]", "").strip()
        time = float(_i)
        data.append(time)

    return data


def fill_dict(data, times, param):
    for i in range(len(times)):
        if i+1 not in data:
            data[i+1] = {}
        data[i+1][param] = times[i]


def get_timedout_sat_info(file):
    data = {}
    with open(file) as f:
        info = f.readlines()

    iteration_num = 0
    for l in info:
        if "OUT OF TIME" in l:
            break
        if "Trying with" in l:
            iteration_num = int(re.match(re_sat_iteration, l).group("iteration"))
            data[iteration_num] = {}

        elif "SAT formula generation time" in l:
            _t = l.split("=")[1].strip()
            data[iteration_num]["ground"] = float(_t)
        elif "Done solver. Round time" in l:
            _s = l.split(":")[1].replace('c', '').strip()
            data[iteration_num]["solve"] = float(_s)

    del_keys = []
    for _i in data.keys():
        if "solve" in data[_i]:
            data[_i]["total"] = data[_i]["ground"] + data[_i]["solve"]
        else:
            del_keys.append(_i)

    for _d in del_keys:
        del data[_d]

    return data


def get_interim_sat_info(file):
    data = {}
    with open(file) as f:
        info = f.readlines()

    for l in info:
        if "Elapsed grounding time" in l and "[" in l:
            times = _extract_times(l)
            fill_dict(data, times, "ground")
        elif "Elapsed solver time" in l and "[" in l:
            times = _extract_times(l)
            fill_dict(data, times, "solve")

    for _i in data.keys():
        data[_i]["total"] = data[_i]["ground"] + data[_i]["solve"]

    return data


def get_final_sat_info(file):
    data = {}
    with open(file) as f:
        info = f.readlines()

    for l in info:
        if "Solved with" in l:
            result = re.match(re_sat, l)
            data["states"] = int(result.group("states"))
        elif "Elapsed total time" in l and "[" not in l:
            _s = l.split(":")[1].strip()
            result = re.match(re_sat_time, _s)
            data["total"] = float(result.group("time"))
        elif "Elapsed grounding time" in l and "[" not in l:
            _s = l.split(":")[1].strip()
            result = re.match(re_sat_time, _s)
            data["ground"] = float(result.group("time"))
        elif "Elapsed solver time" in l and "[" not in l:
            _s = l.split(":")[1].strip()
            result = re.match(re_sat_time, _s)
            data["solve"] = float(result.group("time"))

    return data


def _compute_final_data(interim_data):
    data = {}
    total = 0
    ground = 0
    solve = 0
    for k in interim_data.keys():
        total += interim_data[k]["total"]
        ground += interim_data[k]["ground"]
        solve += interim_data[k]["solve"]

    data["states"] = max(interim_data.keys()) + 2
    data["total"] = total
    data["ground"] = ground
    data["solve"] = solve

    return data


def process_instance(scenario, instance):
    path = f"{OUTPUT_DIR}/{scenario}/{instance}"
    solvers = [f.name for f in os.scandir(path) if f.is_dir()]
    interim_data = {}
    final_data = {}
    timedout_data = {}
    for s in solvers:
        if "asp" in s:
            asp_solved = is_asp_solved(f"{path}/{s}")
            if asp_solved:
                interim_data[s] = get_interim_asp_info(f"{path}/{s}")
                final_data[s] = _compute_final_data(interim_data[s])
            else:
                interim_data[s] = None
                final_data[s] = None
                timedout_data[s] = get_interim_asp_info(f"{path}/{s}")
        elif "sat" in s:
            sat_solved = is_sat_solved(f"{path}/{s}/{instance}.out")
            if sat_solved:
                interim_data[s] = get_interim_sat_info(f"{path}/{s}/{instance}.out")
                final_data[s] = get_final_sat_info(f"{path}/{s}/{instance}.out")
            else:
                interim_data[s] = None
                final_data[s] = None
                if os.path.exists(f"{path}/{s}/{instance}.out"):
                    timedout_data[s] = get_timedout_sat_info(f"{path}/{s}/{instance}.out")

    return final_data, interim_data, timedout_data


def solved_by_all(final_data):
    solved = True
    for key, val in final_data.items():
        if val is None:
            solved = False
    return solved


def process_scenario(scenario):
    path = f"{OUTPUT_DIR}/{scenario}"
    instances = [f.name for f in os.scandir(path) if f.is_dir()]
    final_rows = []
    interim_rows = []
    timedout_rows = []
    for i in instances:
        final_data, interim_data, timedout_data = process_instance(scenario, i)
        if True:  # solved_by_all(final_data):
            for solver in final_data.keys():
                stats = final_data[solver]
                if stats:
                    row = f"{scenario},{i},{solver},{stats['total']},{stats['ground']},{stats['solve']},{stats['states']}{os.linesep}"
                    final_rows.append(row)

            for solver in interim_data.keys():
                if interim_data[solver]:
                    for j in interim_data[solver].keys():
                        stats = interim_data[solver][j]
                        if stats:
                            row = f"{scenario},{i},{solver},{stats['total']},{stats['ground']},{stats['solve']},{j}{os.linesep}"
                            interim_rows.append(row)

            for solver in timedout_data.keys():
                if timedout_data[solver]:
                    for j in timedout_data[solver].keys():
                        stats = timedout_data[solver][j]
                        if stats:
                            row = f"{scenario},{i},{solver},{stats['total']},{stats['ground']},{stats['solve']},{j}{os.linesep}"
                            timedout_rows.append(row)

    return final_rows, interim_rows, timedout_rows


def process(scenario=None):
    headers_f = f"scenario,instance,solver,total-time,ground-time,solve-time,states{os.linesep}"
    headers_i = f"scenario,instance,solver,total-time,ground-time,solve-time,iteration{os.linesep}"
    headers_t = f"scenario,instance,solver,total-time,ground-time,solve-time,iteration{os.linesep}"

    rows_f = [headers_f]
    rows_i = [headers_i]
    rows_t = [headers_t]

    scenarios = [f.name for f in os.scandir(OUTPUT_DIR) if f.is_dir()]
    if scenario is None:
        include = scenarios
    else:
        include = [scenario]

    for d in scenarios:
        if d in include:
            logger.info(f"Processing scenario {d}.")
            r_f, r_i, r_t = process_scenario(d)
            rows_f += r_f
            rows_i += r_i
            rows_t += r_t

    with open(csv_final, "w") as f:
        f.writelines(rows_f)
    with open(csv_interim, "w") as f:
        f.writelines(rows_i)
    with open(csv_timedout, "w") as f:
        f.writelines(rows_t)


def is_asp_solved(output_dir):
    last_file = _get_last_clingo_file(output_dir)
    if last_file is None:
        return False
    return is_asp_satisfiable(f"{output_dir}/{last_file}")


def _get_last_clingo_file(output_dir):
    files = os.listdir(output_dir)
    clingo_files = [c for c in files if c.startswith("clingo")]
    if len(clingo_files) == 0:
        return None
    clingo_ids = [int(re.match(re_clingo, f).group("states")) for f in clingo_files]
    max_id = max(clingo_ids)
    max_idx = clingo_ids.index(max_id)
    last_file = clingo_files[max_idx]
    return last_file


def is_asp_satisfiable(clingo_output):
    with open(clingo_output) as f:
        info = f.readlines()

    for i in info:
        if "UNSATISFIABLE" in i or "TimedOut" in i:
            return False
    return True


def is_sat_solved(output_file):
    if not os.path.exists(output_file):
        return False
    with open(output_file) as f:
        info = f.readlines()

    for i in info:
        if "PLANFOUND!" in i:
            return True

    return False


if __name__ == "__main__":
    logger = logging.getLogger("OutputProcessor")
    coloredlogs.install(level='DEBUG')

    args = get_args()
    OUTPUT_DIR = os.path.expanduser(args['output_path'])
    CSV_FOLDER = os.path.expanduser(args['csv_dir'])

    if args["scenario"] is not None:
        csv_interim = f"{CSV_FOLDER}/{args['scenario']}_interim.csv"
        csv_final = f"{CSV_FOLDER}/{args['scenario']}_final.csv"
        csv_timedout = f"{CSV_FOLDER}/{args['scenario']}_timeout.csv"
        process(scenario=args['scenario'])
    else:
        csv_interim = f"{CSV_FOLDER}/interim.csv"
        csv_final = f"{CSV_FOLDER}/final.csv"
        csv_timedout = f"{CSV_FOLDER}/timeout.csv"
        process()
