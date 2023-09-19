"""
This file has common elements for different planners used in benchmarking FondASP
"""
from abc import ABC, abstractmethod
import configparser
from enum import Enum, auto
import os
import subprocess
from timeit import default_timer as timer
import coloredlogs
import logging
from base.system_utils import ProcessMonitor

class PlannerType(Enum):
    FONDASP = auto()
    FONDSAT = auto()
    PRP = auto()
    PALADINUS = auto()


class Solver(ABC):
    """
    Abstract class to represent a solver that computes FOND solution using different planners.
    """

    def __init__(self, planner_type: PlannerType, config_file:str, config_name: str, location: str = None, use_systemd = False, cpu_quota = None) -> None:
        """_summary_
        Constructor for the Solver class.

        :param planner_type: Type of planner
        :param config_file: Configuration file containing information about the FOND problem
        :param config_name: Name of the section where planner relevant information is stored (e.g. args)
        :param location: Location of the solver (the name of the location should be from the config file)
        :param use_systemd: If systemd-run shoud be used to limit time and memory
        :param cpu_quota: in %. Only valid if used_systemd is True and available
        """
        self.planner_type = planner_type
        self.config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        self.config.read(config_file)
        self.use_systemd = use_systemd
        self.cpu_quota = cpu_quota
        self.location = location if location is not None else self.config["fond"]["location"]
        self.config["fond"]["location"] = location # the config is saved in the output directory, hence important to set it back

        self.config_name = config_name
        self.domain: str | None = None # path to domain file
        self.problem: str | None = None # path to problem file
        self.planner_loc: str | None = None # path to planner's executable file
        self.planner_args: list[str] = []
        self.output_dir: str | None = None # path to output directory
        self.output_file: str | None = None # path to the output file
        self.time_limit: int = 0 # time limit in seconds
        self.grace_time = 5 # allow extra 5 seconds for a planner to exceed the timelimit (for graceful termination)
        self.memory_limit: int = 0 # memory limit in mb
        self.ref: str | None = None
        self.parse() # parse the config file to store the relevant variables

        self.logger = logging.getLogger(f"{planner_type.name}Solver")


        
    def parse(self):
        # where is the solving running from?
        loc: str = self.config["fond"]["location"]

        # planner's executable and extra arguments
        self.planner_loc = os.path.expanduser(self.config[loc][self.planner_type.name.lower()])
        self.planner_args = self.config[self.config_name]["args"].split()

        # domain and problem paths
        problems_dir: str = os.path.expanduser(self.config[loc]["problems"])
        domain: str = os.path.expanduser(self.config["fond"]["domain"])
        problem: str = os.path.expanduser(self.config["fond"]["problem"])
        self.domain = f"{problems_dir}/{domain}"
        self.problem = f"{problems_dir}/{problem}"
        self.problem_id = self.config["fond"]["id"]

        # time and memory limits
        self.time_limit = int(self.config["fond"]["time_limit"])
        self.memory_limit = int(self.config["fond"]["memory_limit"])

        # output directory
        problem_output = os.path.expanduser(self.config["fond"]["output"])
        output_root = f"{os.path.expanduser(self.config[loc]['output_dir'])}/{problem_output}"
        self.ref = self.config[self.config_name]["ref"]
        self.output_dir = f"{output_root}/{self.ref}"  # add a suffix

        # output file for planners output
        self.output_file = f"{self.output_dir}/{self.problem_id}.out"

        # time delay to probe for memory consumption
        self.probe_time = 30


    @abstractmethod
    def solve(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def timed_out(self) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    def memory_exceeded(self) -> bool:
        raise NotImplementedError
    
    def is_solved(self) -> bool:
        """_summary_
        :return: Returns True if the planner has already attempted the given fond problem.
        """
        if os.path.exists(self.output_file):
            return True
        return False
    

    def run(self, cmd: list[str]):
        if self.use_systemd:
            systemd_args = ["systemd-run", "--scope", "-p", f"MemoryMax={self.memory_limit}G", "-p", f"RuntimeMaxSec={self.time_limit}"]
            if self.cpu_quota:
                systemd_args += ["-p", f"CPUQuota={self.cpu_quota}%"]
            
            cmd = systemd_args + cmd
            allow_kill = False
        else:
            allow_kill = True

        # check if the output directory needs to be created
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.logger.info(f"Executing command {cmd}")
        start = timer() # start the timer
        process = subprocess.Popen(cmd, cwd=self.output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)

        # start memory monitor
        monitor = ProcessMonitor(process.pid, self.probe_time, self.output_dir, self.memory_limit, self.time_limit + self.grace_time, allow_kill=allow_kill)
        monitor.start()

        stdout, stderr = process.communicate()

        end = timer() # end timer        
        solve_time = end - start
        self.logger.info(f"Total time taken: {solve_time}s.")

        # save output
        peak_memory = monitor.peak_memory
        monitor.stop_and_store()
        
        with open(self.output_file, "w") as f:
            f.writelines(stdout.decode())
            f.write(os.linesep)
            f.write(f"Total time(sec):{solve_time}{os.linesep}")
            f.write(f"Peak memory(MB):{peak_memory}{os.linesep}")
    
    def get_stats() -> dict:
        raise NotImplementedError
    

class PaladinusSolver(Solver):

    def __init__(self, config_file: str, config_name: str, location: str, use_systemd = False, cpu_quota = None) -> None:
        super().__init__(PlannerType.PALADINUS, config_file, config_name, location, use_systemd=use_systemd, cpu_quota=cpu_quota)
        self.translator = f"{self.planner_loc}/translator-fond/translate.py"
        self.policy_file = f"{self.output_dir}/policy.out"
        self.graph_file = f"{self.output_dir}/policy.dot"
        self.jar = f"{self.planner_loc}/target/paladinus-1.1-jar-with-dependencies.jar"
        self.heap_limit = self.config[config_name].get("heap_limit", None)

    def timed_out(self) -> bool:
        pass

    def memory_exceeded(self) -> bool:
        pass

    def solve(self) -> None:
        if self.heap_limit:
            cmd = ["java", f"-Xmx{self.heap_limit}", "-jar", self.jar, self.domain, self.problem, "-translatorPath", self.translator, "-timeout", str(self.time_limit), "-exportPolicy", self.policy_file] + self.planner_args
        else:
            cmd = ["java", "-jar", self.jar, self.domain, self.problem, "-translatorPath", self.translator, "-timeout", str(self.time_limit), "-exportPolicy", self.policy_file] + self.planner_args
        self.logger.info(f"Calling Paladinus with {self.domain}, {self.problem} and time limit of {self.time_limit}s.")
        self.run(cmd)
      
    def get_stats() -> dict:
        pass

class FondSatSolver(Solver):

    def __init__(self, config_file: str, config_name: str, location: str, use_systemd = False, cpu_quota = None) -> None:
        super().__init__(PlannerType.FONDSAT, config_file, config_name, location, use_systemd=use_systemd, cpu_quota=cpu_quota)
        self.max_states = int(self.config["controller"]["max_states"])

    def timed_out(self) -> bool:
        pass

    def memory_exceeded(self) -> bool:
        pass

    def solve(self) -> None:
        cmd = ["python", self.planner_loc, self.domain, self.problem,  "--time-limit", str(self.time_limit), "--end", str(self.max_states)] + self.planner_args
        self.logger.info(f"Calling FondSat with {self.domain}, {self.problem}, {self.ref} and time limit of {self.time_limit}s.")
        self.run(cmd)

      
    def get_stats() -> dict:
        pass

class PRPSolver(Solver):

    def __init__(self, config_file: str, config_name: str, location: str, use_systemd = False, cpu_quota = None) -> None:
        super().__init__(PlannerType.PRP, config_file, config_name, location, use_systemd=use_systemd, cpu_quota=cpu_quota)

    def timed_out(self) -> bool:
        pass

    def memory_exceeded(self) -> bool:
        pass

    def solve(self) -> None:
        # executable_list = [main_file, domain, instance, "--jic-limit", str(timeout), "--dump-policy", "2"] + extra_args
        cmd = [self.planner_loc, self.domain, self.problem,  "--jic-limit", str(self.time_limit), "--dump-policy", "2"] + self.planner_args
        self.logger.info(f"Calling PRP with {self.domain}, {self.problem}, {self.ref} and time limit of {self.time_limit}s.")
        self.run(cmd)
      
    def get_stats() -> dict:
        pass

class ASPSolver(Solver):

    def __init__(self, config_file: str, config_name: str,  location: str, use_systemd = False, cpu_quota = None) -> None:
        super().__init__(PlannerType.FONDASP, config_file, config_name, location, use_systemd=use_systemd, cpu_quota=cpu_quota)
        self.how = self.config[config_name]["how"]
        self.args = self.config[config_name]["args"]
        self.new_config = f"{self.output_dir}/{self.problem_id}_config.ini"
        self.nd2_domains = ["acrobatics", "doors"] # these domains have a max non-determinism of 6 and 4 and hence require a separate controller
    
    
    def timed_out(self) -> bool:
        pass

    def memory_exceeded(self) -> bool:
        pass

    def save_config(self):
        self.config.add_section("clingo")
        self.config["clingo"]["args"] = self.args
        self.config["clingo"]["how"] = self.how
        self.config["clingo"]["name"] = self.config_name
        self.config["clingo"]["ref"] = self.ref

        scenario = self.config["fond"]["scenario"] 
        if scenario.lower() in self.nd2_domains:
            self.config[self.location]["controller_model"] = self.config[self.location]["controller_model_nd2"] 
        else:
            self.config[self.location]["controller_model"] = self.config[self.location]["controller_model_nd1"] 

        # check if the output directory needs to be created
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
                
        # save config file
        p_id = self.config["fond"]["id"]
        with open(self.new_config, "w") as f:
            self.config.write(f)


    def solve(self) -> None:
        self.save_config()
        cmd = ["python", self.planner_loc, self.new_config, self.how]
        self.logger.info(f"Calling Clingo with {self.domain}, {self.problem} and time limit of {self.time_limit}s.")
        self.run(cmd)
      
    def get_stats() -> dict:
        pass

if __name__ == "__main__":
    config_file = "./output/beam-walk/p11/paladinus/beam-walk_p11.ini"
    # config_file = "./benchmarking/configs/beam-walk/paladinus-1/p11_config.ini"
    paladinus = PaladinusSolver(config_file, "paladinus", "work")
    paladinus.solve()

    # prp = PRPSolver(config_file, "prp", "work")
    # prp.solve()

    # asp = ASPSolver(config_file, "asp1", "work")
    # asp.solve()

    # fondsat = FondSatSolver(config_file, "fondsatMinisat", "work")
    # fondsat.solve()


    

