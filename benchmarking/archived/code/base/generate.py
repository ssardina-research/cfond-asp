"""
This script generates config files from metaconfigs.
This is helpful in running benchmarks.

Assumptions:
1. Domain definitions should start with d.
2. Problem specifications should start with p.
3. Scenarios where domain is specific to problem, the domain and problem files should have same suffix (e.g., d01.pddl, p01.pddl).
   These scenarios should have multiple_domains set to True under fond setting.
"""
import configparser
import copy
import logging
import os
import argparse
import coloredlogs


def generate_config(metaconfig_file, planner, location, time_limit, memory_limit, scenario, domain, problem):
    """
    Generate configs for the given metaconfig file.
    :param metaconfig_file: Metaconfig file
    :param planner: configuration of benchmark (e.g., paladinus, asp4, etc)
    :param location: where will the script run? This must be predefined in the metaconfig files
    :param time_limit: Time limit for the planner
    :param memory_limit: Memory limit for the planner
    :param folder: location of planning instances 
    :param scenario: name of the planning domain/scenario
    :param domain: name of the domain pddl file
    :param problem: name of the problem pddl file
    :return:
    """

    # Step 1. Read the metaconfig file
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(metaconfig_file)

    # Step 2. Update relevant config sections using values defined at the top of this script
    config["fond"]["location"] = location
    config["fond"]["time_limit"] = str(time_limit)
    config["fond"]["memory_limit"] = str(memory_limit)
    config["fond"]["scenario"] = scenario   
    config["fond"]["domain"] = f"{scenario}/{domain}"
    config["fond"]["problem"] = f"{scenario}/{problem}"
    _id = problem[0:-5] # strip the extension
    config["fond"]["id"] = _id
    config["fond"]["output"] = f"{scenario}/{_id}"

    file_name = f"{scenario}_{_id}.ini"
    return save_config(config, location, planner, file_name)


def save_config(config, location, config_name, file_name):
    # output directory
    problem_output = os.path.expanduser(config["fond"]["output"])
    output_root = f"{os.path.expanduser(config[location]['output_dir'])}/{problem_output}"
    ref = config[config_name]["ref"]
    output_dir = f"{output_root}/{ref}"  # add a suffix

    # check if the output directory needs to be created
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    _output_file = f"{output_dir}/{file_name}"
    with open(_output_file, "w+") as f:
        config.write(f)

    return _output_file

        


if __name__ == "__main__":
    metaconfig = "./benchmarking/metaconfigs/benchmarking.ini"
    planner = "prp"
    where = "work"
    time_limit = 100
    memory_limit = 4096
    scenario = "beam-walk"
    problem = "p11.pddl"
    domain = "domain.pddl"

    generate_config(metaconfig, planner, where, time_limit, memory_limit, scenario, domain, problem)

