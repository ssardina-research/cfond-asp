"""
Generate task files for FOND benchmarks as per the format below:
format_version: "2.0"
input_files:
- ../../../benchmarks/acrobatics/domain.pddl
- ../../../benchmarks/acrobatics/p01.pddl

options:
  output: acrobatics/p01

  Example run:

  $ python experiments/benchexec/gen_tasks.py experiments/benchexec/ ./benchmarks 
"""

import argparse
import os
import re

re_1 = r"p(?P<num>[\d]+).pddl"

# default location - can be overridden by CLI --benchmarks
ROOT_BENCHMARKS = "./benchmarks/"
DOMAIN_FILE = "domain.pddl"
KB = {"miner": "miner", "spiky-tireworld": "spikytireworld"}

# scenarios/domains where there is one domain per planning problem
NON_UNIQUE_DOMAIN = ["faults-ipc08"]

def gen_tasks():
    scenarios = [f for f in os.listdir(ROOT_BENCHMARKS) if os.path.isdir(os.path.join(ROOT_BENCHMARKS, f))]
    
    for _domain in scenarios:
        _r = os.path.join(ROOT_BENCHMARKS, _domain)
        _files_dict = {}
        prob_files = [
            f
            for f in os.listdir(_r)
            if re.match(re_1, f)
        ]
        
        for _f in prob_files:    
            _pid = re.match(re_1, _f).group("num")
            if (_domain.lower() in NON_UNIQUE_DOMAIN):  # faults-ipc has a separate domain per problem file
                    _domain_file = f"d{_pid}.pddl"
            else:
                _domain_file = DOMAIN_FILE
                
            _files_dict[_pid] = [_pid, _domain_file, _f]

        for _key in sorted(_files_dict.keys()):
            _value = _files_dict[_key]
            _file_name = f"{_domain}_{_key}.yml"
            with open(os.path.join(TASKS_FOLDER, _file_name), "w") as f:
                f.write('format_version: "2.0"\n')
                f.write("input_files:\n")
                f.write(f"- {PREFIX_DIR}/{_domain}/{_value[1]}\n")
                f.write(f"- {PREFIX_DIR}/{_domain}/{_value[2]}\n")
                f.write("\n")
                f.write("options:\n")
                f.write(f"    output: {_domain}/{_key}\n")
                if _domain in KB.keys():
                    f.write(f"    kb: {KB[_domain]}")


if __name__ == "__main__":
    # CLI options
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Generate APP benchmarks task for BenchExec"
    )
    parser.add_argument(
        "--folder", 
        default="./experiments/benchexec",
        help="place to put the tasks (Default: $(default)s).")

    parser.add_argument(
        "--benchmarks",
        default=ROOT_BENCHMARKS,
        help="Folder where benchmarks are located (Default: $(default)s).)",
    )
    
    parser.add_argument(
        "--prefix", 
        default="../../../benchmarks",
        help="prefix to benchmark folder (Default: $(default)s).")
    
    args = parser.parse_args()

    # "./benchmarks/benchexe/tasks"
    TASKS_FOLDER = os.path.join(args.folder, "tasks")
    PREFIX_DIR = args.prefix

    if not os.path.exists(TASKS_FOLDER):
        os.makedirs(TASKS_FOLDER, exist_ok=True)
        
    gen_tasks()

