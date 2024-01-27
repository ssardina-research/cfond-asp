import argparse
import os
import re
import csv

re_1 = r"p(?P<num>[\d]+).pddl"

HEADER = ['scenario', 'id', 'domain', 'problem']
INSTANCES = []

# PROBLEMS_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, "problems"))
PROBLEMS_ROOT = "./benchmarking/problems"
CUSTOM_REASONING = ['faults-ipc08'] # this scenario doesn't have a unique domain
INSTANCE_FILE = "instances.csv"



def add_instances(scenario):
    global INSTANCES

    files = [f for f in os.listdir(os.path.join(PROBLEMS_ROOT, scenario)) if f.endswith(".pddl")]
    problem_files = [f for f in files if f.startswith("p")]
    domain_file = [f for f in files if f.lower().startswith("d")][0]

    files_dictionary = {}
    for _f in problem_files:
        _id = int(re.match(re_1, _f).group("num"))
        files_dictionary[_id] = _f

    for _id in sorted(files_dictionary.keys()):
        _problem = os.path.join(PROBLEMS_ROOT, scenario, files_dictionary[_id])
        _id = _problem.split(os.sep)[-1][0:-5]
        _domain = os.path.join(PROBLEMS_ROOT, scenario, domain_file)
        print([scenario, _id, _domain, _problem])
        INSTANCES.append([scenario, _id, _domain, _problem])


def add_faults_instances():
    global INSTANCES

    scenario = "faults-ipc08"
    files = [f for f in os.listdir(os.path.join(PROBLEMS_ROOT, scenario)) if f.endswith(".pddl")]
    problem_files = [f for f in files if f.startswith("p")]
    domain_files = [f for f in files if f.lower().startswith("d")]

    files_dictionary = {}
    for _f in problem_files:
        _seq = int(re.match(re_1, _f).group("num"))
        _id = re.match(re_1, _f).group("num")
        _domain_file = f"d{_id}.pddl"
        if _domain_file in domain_files:
            files_dictionary[_seq] = (_f, _domain_file)
        else:
            print(f"Error! could not find domain file for {_f}")

    for _id in sorted(files_dictionary.keys()):
        _p, _d = files_dictionary[_id]
        _problem = os.path.join(PROBLEMS_ROOT, scenario, _p)
        _domain = os.path.join(PROBLEMS_ROOT, scenario, _d)
        INSTANCES.append([scenario, f"p{_id:02d}", _domain, _problem])



if __name__ == "__main__":
    # CLI options
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Generate the instance CSV file for a folder of problems."
    )
    parser.add_argument("problem_folder",
        help="Path to the root where all scenarios/problems are located.")
    parser.add_argument("instance_file",
        help="Name of the CSV instance file to use")
    args = parser.parse_args()

    PROBLEMS_ROOT = args.problem_folder
    INSTANCE_FILE = os.path.join(PROBLEMS_ROOT, args.instance_file)

    # callect all the scenarios as folders inside PROBLEMS_ROOT
    scenarios = [f for f in os.listdir(PROBLEMS_ROOT) if os.path.isdir(os.path.join(PROBLEMS_ROOT, f))]
    scenarios.sort()

    for _scenario in scenarios:
        if _scenario not in CUSTOM_REASONING:
            add_instances(_scenario)
        else:
            match(_scenario):
                case "faults-ipc08":
                    add_faults_instances()

    # write the CSV file
    with open(INSTANCE_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(HEADER)
        writer.writerows(INSTANCES)

