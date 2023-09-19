"""
This script tests different clingo configurations and solvers on a sample of instances.
Note: Acrobatics and doors has nd effect size of >2
"""
import configparser
import logging
import os.path
import subprocess

import coloredlogs

instances = ["p01", "p03"]
# configurations = ["", "--configuration=frumpy", "--configuration=tweety", "--configuration=trendy", "--configuration=crafty", "--configuration=jumpy", "--configuration=handy",
#                   "--sat-p=2 --trans-ext=integ --eq=3 --reverse-arcs=2 --shuffle=1"]

configurations = {"custom": "--sat-p=2 --trans-ext=integ --eq=3 --reverse-arcs=2 --shuffle=1", "acclingo": "--backprop  --trans-ext=dynamic --sat-prepro=2,10,25,0,0 --eq=0  --block-restarts=0 --heuristic=Vsids,95 --opt-strategy=bb,lin --restarts=x,128,1.5 --strengthen=local,all,yes --lookahead=no --update-lbd=no    --configuration=auto --init-watches=least --loops=no --opt-heuristic=0 --otfs=2 --partial-check=0 --rand-freq=0.0 --reset-restarts=no --reverse-arcs=1 --save-progress=180 --score-other=loop --sign-def=asp --del-cfl=no --counter-restarts=3,10 --del-glue=2,0 --del-grow=1.1,20.0 --del-init=3.0,1023,9000 --deletion=basic,75,activity --no-contraction --del-estimate=0 --del-max=250000 --del-on-restart=0 --score-res=set --vsids-progress=no"}

models = ["controller.lp"]
solve = ["solve"]
location = "work"
# config_files = ["acrobatics.ini", "beam-walk.ini", "blocksworld.ini", "doors.ini", "earth-obs.ini", "elevators.ini", "faults.ini", "first-resp.ini", "islands.ini",
#                 "linear-tireworld.ini", "miner.ini", "spiky-tireworld.ini", "tireworld.ini", "tireworld-truck.ini", "triangle-tireworld.ini"]

config_files = ["beam-walk.ini", "blocksworld.ini", "earth-obs.ini", "elevators.ini", "faults.ini", "first-resp.ini", "islands.ini",
                "miner.ini", "spiky-tireworld.ini", "tireworld.ini", "tireworld-truck.ini", "triangle-tireworld.ini"]

output_dir = "./output"
tmp_dir = f"{output_dir}/tmp"

asp_planner = "./src/python/main.py"


def parse_config(config_file: str):
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(config_file)

    return config


def run():
    for _c in config_files:
        _f = f"./configs/{_c}"
        config = parse_config(_f)

        for instance in instances:
            counter = 1
            for config_name, configuration in configurations.items():
                for i in range(len(models)):
                    logger.info(f"Exploring {instance} for domain {_c}.")
                    model = models[i]
                    solve_cmd = solve[i]

                    config["fond"]["id"] = instance
                    config["fond"]["determiniser"] = "prp"
                    config["fond"]["location"] = location
                    config[location]["controller_model"] = f"${{root}}/src/asp/{model}"
                    config["clingo"]["ref"] = f"{config_name}-{model}"
                    config["clingo"]["args"] = f"--stats {configuration}"

                    _tmp_config = f"{tmp_dir}/{_c[0:-4]}_{instance}_{counter}.ini"
                    with open(_tmp_config, 'w') as configfile:
                        config.write(configfile)

                    solver_folder = f"{output_dir}/{config['fond']['scenario']}/{config['fond']['id']}/asp-{config['clingo']['ref']}"
                    if not os.path.exists(solver_folder):
                        exec_str = f"python {asp_planner} {_tmp_config} {solve_cmd}"
                        subprocess.call(exec_str, shell=True)

                    counter += 1


if __name__ == "__main__":
    logger = logging.getLogger("Explorer")
    coloredlogs.install(level='DEBUG')
    run()
