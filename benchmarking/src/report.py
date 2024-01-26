import argparse
import os

import domain_spec
from domain_spec import REPORT_FILE

OUTPUT = []

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
                sat, time_solve, time_out, memory_used, memory_exceeded, policy_size = domain_spec.get_stats(_path)

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
