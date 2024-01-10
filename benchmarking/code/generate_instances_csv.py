import os
import re

re_1 = r"p(?P<num>[\d]+).pddl"

HEADERS = f"scenario,domain,instance,output{os.linesep}"
INSTANCES = [HEADERS]

# PROBLEMS_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, "problems"))
PROBLEMS_ROOT = "./benchmarking/problems"
CUSTOM_REASONING = ['faults-ipc08'] # this scenario doesn't have a unique domain
INSTANCE_FILE = os.path.join(PROBLEMS_ROOT, "instances.csv")

scenarios = [f for f in os.listdir(PROBLEMS_ROOT) if os.path.isdir(os.path.join(PROBLEMS_ROOT, f))]


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
        _output = os.path.join(scenario, files_dictionary[_id][0:-5])
        _domain = os.path.join(PROBLEMS_ROOT, scenario, domain_file)
        INSTANCES.append(f"{scenario},{_domain},{_problem},{_output}{os.linesep}")


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
        _output = os.path.join(scenario, _p[0:-5])
        _domain = os.path.join(PROBLEMS_ROOT, scenario, _d)
        INSTANCES.append(f"{scenario},{_domain},{_problem},{_output}{os.linesep}")


for _scenario in scenarios:
    if _scenario not in CUSTOM_REASONING:
        add_instances(_scenario)

    else:
        match(_scenario):
            case "faults-ipc08":
                add_faults_instances()

with open(INSTANCE_FILE, "w+") as f:
    f.writelines(INSTANCES)