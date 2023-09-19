"""
Main file to run benchmarks for different planners and domains.
The script will run a planner on all instances of a domain for a given location (see benchmark.ini for locations and planners)

Assumptions:
1. Given config files has sections for where to run the benchmarks and which planners to use
2. All problem files start with "p"
3. All domain files start with "d". 
   - The there is a single domain it should be named domain.pddl. 
   - If there is one domain per problem, then they should be named d<num>.pddl and p<num>.pddl, respectively.
4. The respective domain/scenario folders contain only relevant pddl files

IMPORTANT: The script uses systemd-run that requires sudo previliges. However, the python virtual environment should be available as root.
One way to do this is using the -E option and absolute path to Python:
sudo -E env "PATH=$PATH" python ./benchmarking/code/run.py ./benchmarking/metaconfigs/benchmarking.ini  beam-walk paladinus-mem  --where work
"""

import argparse
import configparser
import logging
import shutil
import coloredlogs
import os
import re
from base.generate import generate_config
from base.planners import ASPSolver, FondSatSolver, PRPSolver, PaladinusSolver

re_problem = r"p(?P<number>[\d]+).pddl"

time_limit = None
memory_limit = None # in GB
systemd_exists = False
systemd_cmd = "systemd-run"


def check_systemd():
    global systemd_exists
    """
    systemd-run is used to specify limits for each process
    e.g., systemd-run --scope -p MemoryMax=4G RuntimeMaxSec=3600
    """
    path = shutil.which(systemd_cmd)
    if path:
        systemd_exists = True
        logger.info("systemd-run exists and will be used.")
    else:
        systemd_exists = False
        logger.info("systemd-run not found.")

def get_problems(problems_dir):
    """
    Get planning problems from the given directory.
    The script automatically checks if the domain file is unique or paired with a problem file.
    """
    planning_files = [f for f in os.listdir(problems_dir) if f.endswith(".pddl")]
    problem_files = [f for f in planning_files if f.startswith("p")]
    domain_files = [f for f in planning_files if f.startswith("d")]
    numbers = [re.search(re_problem, p).group("number") for p in problem_files]
    
    if len(domain_files) == 1:
        return {f"p{i}.pddl": "domain.pddl" for i in numbers}
    else:
        return {f"p{i}.pddl": f"d{i}.pddl" for i in numbers}


def run_benchmark(config_file, scenario, planner, where, time_limit, memory_limit, cpu_quota, skip):
    """_summary_
    :param config_file: Benchmark configuration file
    :param scenario: Name of the planing scenario
    :param planner: Name of the planner config
    :param where: Location where the script will run from
    :param time_limit: Time limit for each instance
    :param memory_limit: Memory limit for each instance
    :param cpu_quota: Limit on CPU quota in %
    :param skip: If attempted problems should be skipped (solved, timed out or exceeded memory are considered attempted.)
    """
    # parse the benchmarking config
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(config_file)
    
    config_time_limit = config["benchmarking"]["time_limit"]
    config_memory_limit = config["benchmarking"]["memory_limit"]
    config_cpu_quota = config["benchmarking"]["cpu_quota"]

    time_limit = time_limit if time_limit is not None else config_time_limit
    memory_limit = memory_limit if memory_limit is not None else config_memory_limit
    cpu_quota = cpu_quota if cpu_quota is not None else config_cpu_quota

    problems_dir = config[where]["problems"]
    scenario_dir = os.path.expanduser(f"{problems_dir}/{scenario}")

    # get the problems from the given domain folder
    problems = get_problems(scenario_dir)
    logger.info(f"Found {len(problems)} problems for the {scenario}.")

    # solve each problem one by one using the given planner
    numbers = sorted([re.search(re_problem, p).group("number") for p in problems.keys()])
    for n in numbers:
        problem = f"p{n}.pddl"
        domain = problems[problem]
        
        # Step 1. First generate the config specific to the planner, location, and problem
        # This is important as later one we can retrieve which configuration was used.
        problem_config = generate_config(config_file, planner, where, time_limit, memory_limit, scenario, domain, problem)

        # Step 2. Call the relevant planner!
        planner_type = config[planner]["type"]
        match planner_type:
            case "prp":
                solver = PRPSolver(problem_config, planner, where, use_systemd=systemd_exists, cpu_quota=cpu_quota)
            case "paladinus":
                solver = PaladinusSolver(problem_config, planner, where, use_systemd=systemd_exists, cpu_quota=cpu_quota)
            case "fondsat":
                solver = FondSatSolver(problem_config, planner, where, use_systemd=systemd_exists, cpu_quota=cpu_quota)
            case "fondasp":
                solver = ASPSolver(problem_config, planner, where, use_systemd=systemd_exists, cpu_quota=cpu_quota)

        if skip and solver.is_solved():
            logger.info(f"Skipping {problem_config}.")
            continue

        solver.solve()


def main():
    # CLI options
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Benchmarking script for running a planner on all problems of a domain."
    )
    parser.add_argument("config_file",
                        help="Config file with the FOND instance details.")
    parser.add_argument("domain",
                        help="Name of the FOND domain.")
    parser.add_argument("planner",
                        help="Name of the planner to execute.")
    parser.add_argument("--where",
                        help="Where to execute the system.", default="work", type=str)
    parser.add_argument("--time_limit",
                        help="Time limit per instance in seconds.", default=None, type=int)
    parser.add_argument("--memory_limit",
                        help="Memory limit per instance in GB.", default=None, type=int)
    parser.add_argument("--cpu",
                        help="Quota on CPU usage in %.", default=None, type=int)
    parser.add_argument("--skip",
                        help="Skip solved instances.", default=False, type=bool)
    
    args = parser.parse_args()
    config_file = args.config_file
    domain = args.domain
    planner = args.planner
    where = args.where
    time_limit = args.time_limit
    memory_limit = args.memory_limit
    cpu_quota = args.cpu
    skip = args.skip
    
    check_systemd()
    run_benchmark(config_file, domain, planner, where, time_limit, memory_limit, cpu_quota, skip)
    

if __name__ == "__main__":
    logger = logging.getLogger(f"PlanningBenchmarks")
    coloredlogs.install(level='DEBUG')
    main()