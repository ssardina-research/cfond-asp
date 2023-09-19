from datetime import datetime
import logging
import os
import re
import signal
import threading
import time
from timeit import default_timer as timer
import coloredlogs
from cpuinfo import get_cpu_info
import platform
import psutil

re_config = r"[a-z,A-Z]+(?P<index>[\d]+)_config.ini"
MB_CONVERSION = 1024 * 1024


class ProcessMonitor(threading.Thread):
    """_summary_
    Class to monitor time and memory consumption of a process.
    If memory and time limits are given, then the process is killed if those limits are exceeded.
    """
    def __init__(self, pid, sleep_time, output_folder, memory_limit=None, time_limit=None, allow_kill=False):
        """_summary_
        Constructor
        :param pid: ID of the process to monitor
        :param sleep_time: Delay between monitoring
        :param output_folder: folder to store the monitoring stats data 
        :param memory_limit: Memory limit in MB, defaults to None
        :param time_limit: Time limit in seconds, defaults to None
        :param allow_kill: Check if this monitor should kill the process if limits are exceeded
        """
        threading.Thread.__init__(self)
        self.pid = pid
        self.process = psutil.Process(pid)
        self.sleep_time = sleep_time
        self.output_folder = output_folder
        self.stats_file = "memory_usage.csv"
        self.outcome_file = "memory.out"
        self.memory_limit = memory_limit
        self.time_limit = time_limit
        self.allow_kill = allow_kill
        self._stop = False
        self.data = [f"time,counter,name,memory{os.linesep}"]
        self.peak_memory = 0
        self.start_time = None # initial timer
        self.logger = logging.getLogger("MemoryMonitor")
        self.limit_exceeded = False

    def run(self) -> None:
        counter = 1
        is_finished = False
        self.start_time = timer() # start the timer
        while not self._stop:
            try:
                self.probe_memory_usage(counter) # probe memory usage
                if self.allow_kill:
                    self.check_limit_exceeded() # check if time or memory limit have been exceeded
                counter += 1 # increment the counter

                # check if the process terminated before the limits were exceeded. In this case we should stop monitoring.
                is_finished = self.process.status() in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD, psutil.STATUS_STOPPED)
                if is_finished:
                    self._stop = True

                time.sleep(self.sleep_time) # sleep
            except psutil.NoSuchProcess:
                self._stop = True

    def probe_memory_usage(self, counter):
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S") # dd/mm/YY H:M:S

        # get the used memory
        rss = self.get_process_memory(self.pid) / MB_CONVERSION
        total_memory = rss

        # store the usage by parent
        row = f"{dt_string},{counter},parent,{rss}{os.linesep}"
        self.data.append(row)
        
        # get the children of the given process and probe their usage
        children = self.process.children(recursive=True)
        for c in children:
            child_rss = self.get_process_memory(c.pid) / MB_CONVERSION
            total_memory += child_rss
            row = f"{dt_string},{counter},{c.name()},{child_rss}{os.linesep}"
            self.data.append(row)
        
        # update the peak memory used so far
        if self.peak_memory < total_memory:
            self.peak_memory = total_memory

        # store the total memory used by the given process
        row = f"{dt_string},{counter},total,{total_memory}{os.linesep}"
        self.data.append(row)
        # self.logger.warning(f"{counter},total,{total_memory}")

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, value):
        self._stop = value

    def stop_and_store(self):
        self.logger.debug(f"Peak memory usage was {self.peak_memory} MB, time consumed was {timer() - self.start_time}.")
        if not self.limit_exceeded:
            self.store_outcome("False")
        self.store_stats()
        self._stop = True

    def store_stats(self):
        with open(f"{self.output_folder}/{self.stats_file}", "w+") as f:
            f.writelines(self.data)

    @staticmethod
    def get_process_memory(pid):
        process = psutil.Process(pid)
        return process.memory_info().rss

    def check_limit_exceeded(self):
        self.check_memory_exceeded()
        self.check_time_exceeded()

    def check_time_exceeded(self):
        if self.time_limit:
            time_consumed = timer() - self.start_time
            if time_consumed> self.time_limit:
                self.limit_exceeded = True
                self.store_outcome("True (time)")
                self.store_stats()
                self.kill_process()

    def check_memory_exceeded(self):
        if self.memory_limit:
            if self.peak_memory > self.memory_limit:
                self.limit_exceeded = True
                self.store_outcome("True (memory)")
                self.store_stats()
                self.kill_process()

    def store_outcome(self, status):
        with open(f"{self.output_folder}/{self.outcome_file}", "w+") as f:
            f.write(f"PeakMemory(MB):{self.peak_memory}{os.linesep}")
            f.write(f"Limit:{self.memory_limit}{os.linesep}")
            f.write(f"LimitExceeded:{status}{os.linesep}")

    def kill_process(self):
        self._stop = True
        for child in self.process.children(recursive=True):
            child.kill()
        self.process.kill()
        self.logger.error(f"Process {self.pid}:{self.process.name} killed as limit exceeded.")


def get_execution_order(output_dir):
    """
    Returns the clingo file representing the highest iteration.
    :param output_dir:
    :return:
    """
    files = os.listdir(output_dir)
    config_files = [c for c in files if c.endswith("config.ini") and not c.startswith(".")]

    config_ids = {int(re.match(re_config, f).group("index")): f for f in config_files}
    sorted_ids = sorted(config_ids.keys())
    sorted_files = [config_ids[i] for i in sorted_ids]

    return sorted_files


def print_system_info():
    print("------------------------------------------------------------------------------")
    for key, value in get_cpu_info().items():
        print("{0}: {1}".format(key, value))

    print(f"Platform:{platform.system()}")
    print(f"Platform version:{platform.version()}")
    print(f"Platform release:{platform.release()}")
    print(f"Memory:{str(round(psutil.virtual_memory().total / (1024.0 **3)))} GB")
    print("------------------------------------------------------------------------------")


if __name__ == "__main__":
    print_system_info()
