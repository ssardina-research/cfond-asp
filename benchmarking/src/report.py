import argparse
import os
import csv

import domain_spec
from domain_spec import REPORT_FILE

OUTPUT = []

def report(output_folder):
    """
    The report assumes the folder structure is the same as created by this benchmark: scenario/problem/solver
    """

    # grab each scenario folder (each folder in the experiment path is a scenario)
    scenarios = [s for s in os.listdir(output_folder) if os.path.isdir(os.path.join(output_folder, s))]
    scenarios.sort()

    report_csv_lines = []
    for s in scenarios:
        _d = os.path.join(output_folder, s)

        # get now all the problems in the scenario, loop on each
        problems = [p for p in os.listdir(_d) if os.path.isdir(os.path.join(_d, p))]
        problems.sort()
        for p in problems:
            _p = os.path.join(os.path.join(output_folder, s, p))

            # get all solvers used, and loop on each
            solvers = [s for s in os.listdir(_p) if os.path.isdir(os.path.join(_p, s))]
            for sol in solvers:
                _path = os.path.join(output_folder, s, p, sol)

                row = [s, p, sol] + [*domain_spec.get_stats(_path)]
                print(row)
                report_csv_lines.append(row)

    # write the csv report
    with open(os.path.join(output_folder, REPORT_FILE), 'w', newline='') as csvfile:
        # first one is header of csv report
        header_names = ["domain","instance","solver"] + domain_spec.REPORT_HEADER
        writer = csv.writer(csvfile)

        writer.writerow(header_names)
        writer.writerows(report_csv_lines)


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
