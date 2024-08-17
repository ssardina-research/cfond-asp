"""
Generate task files for FOND benchmarks as per the format below:

    format_version: "2.0"
    input_files:
    - ../../../benchmarks/acrobatics/domain.pddl
    - ../../../benchmarks/acrobatics/p01.pddl

    options:
    output: acrobatics/p01

  Example run:

  $ python gen_tasks.py benchexec/ ../benchmarks
"""

import argparse
import os
import re

re_1 = r"p(?P<num>[\d]+).pddl"

# default location - can be overridden by CLI --benchmarks
DOMAIN_FILE = "domain.pddl"
KB = {"miner": "miner", "spiky-tireworld": "spikytireworld"}

# scenarios/domains where there is one domain per planning problem
NON_UNIQUE_DOMAIN = ["faults-ipc08"]


def gen_tasks(folder_benchmark, folder_tasks, prefix_path):
    scenarios = [
        f
        for f in os.listdir(folder_benchmark)
        if os.path.isdir(os.path.join(folder_benchmark, f))
    ]

    for _domain in scenarios:
        _r = os.path.join(folder_benchmark, _domain)
        _files_dict = {}
        prob_files = [f for f in os.listdir(_r) if re.match(re_1, f)]

        for _f in prob_files:
            _pid = re.match(re_1, _f).group("num")
            if (
                _domain.lower() in NON_UNIQUE_DOMAIN
            ):  # faults-ipc has a separate domain per problem file
                _domain_file = f"d{_pid}.pddl"
            else:
                _domain_file = DOMAIN_FILE

            _files_dict[_pid] = [_pid, _domain_file, _f]

        for _key in sorted(_files_dict.keys()):
            _value = _files_dict[_key]
            _file_name = f"{_domain}_{_key}.yml"
            with open(os.path.join(folder_tasks, _file_name), "w") as f:
                f.write('format_version: "2.0"\n')
                f.write("input_files:\n")
                f.write(f"- {prefix_path}/{_domain}/{_value[1]}\n")
                f.write(f"- {prefix_path}/{_domain}/{_value[2]}\n")
                f.write("\n")
                f.write("options:\n")
                f.write(f"    output: {_domain}/{_key}\n")
                if _domain in KB.keys():
                    f.write(f"    kb: {KB[_domain]}")


if __name__ == "__main__":
    # CLI options
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Generate benchmarks task for BenchExec"
    )

    parser.add_argument(
        "benchmark",
        help="Folder where benchmarks are located.",
    )

    parser.add_argument(
        "tasks",
        help="folder to put the tasks (in a 'tasks' subfolder).",
    )

    parser.add_argument(
        "--prefix",
        default="../../../benchmarks",
        help="prefix to benchmark folder relative to task files (Default: %(default)s).",
    )
    args = parser.parse_args()
    print(args)

    # setup folder for tasks files
    folder_tasks = os.path.join(args.tasks, "tasks")
    if not os.path.exists(folder_tasks):
        os.makedirs(folder_tasks, exist_ok=True)

    gen_tasks(args.benchmark, folder_tasks, args.prefix)
