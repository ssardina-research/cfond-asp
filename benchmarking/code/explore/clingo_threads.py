"""
Explore the distribution of run times for clingo based on number of threads.
"""
import logging
import os

import coloredlogs

from benchmarking.scripts.explore.report import parse_file
from utils.helper_clingo import execute_asp

output_dir = "./output/clingo"
threads = [1, 2, 4, 6, 8, 10]
num_samples = 100
instance_dir = "../../benchmarking/scripts/explore/instance"
instances = {1: "instance1.lp", 2: "instance2.lp", 3: "instance3.lp", 4: "instance4.lp"}
model = "../../src/asp/controller.lp"
clingo_cmd = "clingo"
clingo_args = ""
ref = 1
instance_states = {1: [8, 9], 2: [30, 31], 3: [9, 10], 4: [13, 14]}


def run():
    for t in threads:
        for instance_num, instance in instances.items():
            num_states = instance_states[instance_num]
            for s in num_states:
                logger.info(f"Simulating {t} threads for {s} states.")
                for i in range(num_samples):
                    file_name = f"{output_dir}/{instance_num}_{s}_{t}_{i}.out"
                    execute_asp(clingo_cmd, [f"--stats", f"-t {t}", f"-c numStates={s}"], [f"{instance_dir}/{instance}", model], output_dir, file_name)


def process():
    data = [f"sim,instance_num, num_states,num_threads,cpu_time,time,solve_time,choices,conflicts,restarts,variables,constraints{os.linesep}"]
    _files = [f for f in os.listdir(output_dir) if f.endswith("out")]
    for _f in _files:
        tokens = _f[:-4].split("_")
        i = tokens[0]
        s = tokens[1]
        t = tokens[2]
        n = tokens[3]
        info = parse_file(f"{output_dir}/{_f}")
        if info['sat'] > info['unsat']:
            solve_time = info['sat']
        else:
            solve_time = info['unsat']
        row = f"{i},{n},{s},{t},{info['cpu_time']},{info['total_time']},{solve_time},{info['choices']},{info['conflicts']},{info['restarts']},{info['variables']},{info['constraints']}{os.linesep}"
        data.append(row)

    with open("./clingo_threads.csv", "w") as f:
        f.writelines(data)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    coloredlogs.install(level='INFO')
    # run()
    process()


