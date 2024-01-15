
#TODO
# --------
# 1. Implement more precise is_solved
# 2. Add report functionality
# --------

import argparse
import asyncio
import traceback
import os
import shutil
import csv
import atexit
from asyncio.queues import Queue
from datetime import datetime
from report import is_solved
from monitor import Monitor
from task import Task, TaskStatus
import json
from datetime import datetime

PLANNER = "./src/python/main.py"
RESULTS_FILE = "results.csv"
SKIP: bool = False
CSV_PATH: str = None
BATCH_SIZE: int = 0
OUTPUT_ROOT: str = None
TASK_QUEUE = Queue()
TASKS = {}
ACTIVE_TASKS = {}
FINISHED_TASKS = {}
TIME_LIMIT = None
MEMORY_LIMIT = None
CONFIG_FILE = str
SOLVERS = {}
SCENARIOS = []

total_count = 0
lock = asyncio.Lock()
monitor: Monitor

def create_folder(path: str, delete: bool = False):
    path = os.path.expanduser(path)
    if os.path.exists(path) and delete:
        shutil.rmtree(path)

    os.makedirs(path, exist_ok=True)


async def prepare_tasks(queue: Queue):
    """
    Initialising benchmarks involves:

        1. Set the static time and memory limit for Task
        2. Ensuring output directory exists (does not delete the output directory as one may want to re-run a subset of instances).
        3. Copy the config file in the output folder.
        4. Reading the input csv files for instance information and for each entry in the csv file creating a task.
        5. If the tasks needs to be solved (e.g., checking for skip) then adding it to the queue.
        6. Initalising the monitor (to track memory usage and display status).
    """
    global monitor, total_count

    # 1. set the time and memory limits
    Task.time_limit = TIME_LIMIT
    Task.memory_limit = MEMORY_LIMIT

    # 2. create the output root directory if it doesn't exist
    create_folder(OUTPUT_ROOT, delete=False)

    # 3. copy the config file to output
    now = datetime.now()
    dt_string = now.strftime("%d%b%Y_%H%M")

    config_src = os.path.join(CONFIG_FILE)
    config_dest = os.path.join(OUTPUT_ROOT, f"config_{dt_string}.json")
    shutil.copyfile(config_src, config_dest)

    # 4. Read input CSV file and create tasks
    with open(CSV_PATH) as instances:
        _counter = 1
        for instance in csv.DictReader(instances):
            _scenario = instance["scenario"]
            _domain = instance["domain"]
            _problem = instance["instance"]
            _problem_id = _problem.split(os.sep)[-1][0:-5]
            _output = instance["output"]

            for solver_id, solver_info in SOLVERS.items():
                _output_path = os.path.join(OUTPUT_ROOT, _output, solver_id)
                _is_solved = is_solved(os.path.abspath(_output_path))
                _should_run = (not SKIP or not _is_solved) and _scenario in SCENARIOS

                # 5. add task to queue (if it should run)
                if _should_run:
                    solver_args = solver_info["args"]

                    for f in [_domain, _problem]:
                        if not os.path.exists(f):
                            print(f"File {f} does not exist. Aborting..")
                            exit(1)

                    cmd = f"python {PLANNER} {_domain} {_problem} {solver_args} --output {_output_path}"
                    task = Task(_counter, _scenario, _problem_id, cmd, solver_id, _output_path)
                    await queue.put(task)
                    _counter += 1

    # 6. initialise monitor
    total_count = queue.qsize()

    if input(f"About to run {total_count} tasks. To continue type 'Y' ").lower() == "y":
        monitor = Monitor(total_count)
        monitor.start()
    else:
        exit(0)


async def run_tasks(queue: Queue):
    """
    Run benchmarks by creating the required number of consumers and starting them.
    """
    task_runners = []
    for _i in range(BATCH_SIZE):
        _consumer = asyncio.create_task(consume_task(queue, f"q{_i}"))
        task_runners.append(_consumer)

    # wait for all conusmers to finish the allocated tasks
    await asyncio.gather(*task_runners, return_exceptions=True)


async def consume_task(queue: Queue, name: str):
    """
    This function implements a consumer. A consumer in this context takes a pending task from the queue and runs it.
    It works as follows:
    1. Check if queue is empty or not. If queue is empty the function finishes. Else, it gets the next task from the queue.
    2. To run a task, it creates a subproces shell and doesn't care about its output to stdout/stderr
    3. It then stores the pid (this is the pid of the shell), start time, the task status.
    4. It then waits for the task to finish
    """

    # 1. While queue is not empty, pick a task from queue and run it
    while not queue.empty():

        ## get the next id and the assocated command to run
        task:Task = await queue.get()
        task.queue = name
        
        # 2. run the task by creating a subprocess
        try:
            # print(task.cmd)
            proc = await asyncio.create_subprocess_shell(task.cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL, preexec_fn=os.setsid)

            # 3. Store the relevant information
            task.pid = proc.pid
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()
            await update_counts(task)

            # 4. Wait for the process to finish
            await asyncio.wait_for(proc.communicate(), timeout=TIME_LIMIT)
            task.status = TaskStatus.FINISHED
            await update_counts(task)

        except asyncio.TimeoutError:
            # task timed out (ideally, should not happen as the underlying solver should quit on its own)
            task.status = TaskStatus.ERROR
            await update_counts(task)
        except Exception:
            task.status = TaskStatus.ERROR
            await update_counts(task)
            traceback.print_exc()

async def update_counts(task: Task):
    """
    Keep track of tasks that are active or finished
    """
    global ACTIVE_TASKS, FINISHED_TASKS
    _id: str = f"{task.scenario}_{task.solver}_{task.id}"
    async with lock:
        match task.status:
            case TaskStatus.RUNNING:
                ACTIVE_TASKS[_id] = task

            case TaskStatus.FINISHED:
                if not task.memory_exceeded:
                    task.store_memory()  # store the last known max memory used by this task
                FINISHED_TASKS[_id] = task
                del ACTIVE_TASKS[_id]

            case TaskStatus.ERROR:
                FINISHED_TASKS[_id] = task
                del ACTIVE_TASKS[_id]

    monitor.update(ACTIVE_TASKS, len(FINISHED_TASKS))
    if len(FINISHED_TASKS) == total_count:
        monitor.stop = True


def parse_config():
    """
    Parse the config json file for resource limits and solver configs
    """
    global TIME_LIMIT, MEMORY_LIMIT, SOLVERS, SCENARIOS
    try:
        with open(CONFIG_FILE, "r") as read_file:
            config = json.load(read_file)

        # Time and memory restrictions
        TIME_LIMIT = int(config["time_limit"])
        MEMORY_LIMIT = int(config["memory_limit"])

        # solvers information
        solvers_to_run = config["run"]
        for _id in solvers_to_run:
            _args = f"--timeout {TIME_LIMIT} {config['solvers'][_id]['args']}"
            SOLVERS[_id] = {"args": _args}

        # scenarios
        SCENARIOS = config["scenarios"][:]

    except Exception:
        print("Cannot parse config file.")
        traceback.print_exc()
        exit(1)

async def run_experiment():
    """
    Run benchmarks by first initialising all the tasks and then running them by using task consumers.
    """
    await prepare_tasks(TASK_QUEUE)
    await run_tasks(TASK_QUEUE)


def kill_tasks():
    for _, task in ACTIVE_TASKS.items():
        task.kill()

@atexit.register
def goodbye():
    kill_tasks()
    print("Bye Bye!")


if __name__ == "__main__":
    # CLI options
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Benchmarking script to run FOND instances using CFONDASP planner."
    )
    parser.add_argument("csv",
                        help="Path to csv file containing information about instances.")
    parser.add_argument("config",
                        help="Path to config file containing information about solvers.")
    parser.add_argument("--output",
                        default=os.path.join(".", "output"),
                        help="Path to root output directory where all solving information will be stored.")
    parser.add_argument("--mode",
                        default="run",
                        help="Functionality of the system to execute %(default)s.",
                        choices=["run", "report"])
    parser.add_argument('-n', '--num',
                        dest="batch_size",
                        type=int,
                        default=2,
                        help='Number of instances to solve in parallel %(default)s')
    parser.add_argument('--skip',
                        default=False,
                        action='store_true',
                        help='If solved instances should be skipped')

    args = parser.parse_args()

    # store the passed arguments
    what_to_do = args.mode
    CSV_PATH = args.csv
    OUTPUT_ROOT = args.output
    SKIP = args.skip
    BATCH_SIZE = args.batch_size
    CONFIG_FILE = args.config

    # parse the config before doing anything
    parse_config()

    match what_to_do:
        case "run":
            try:
                asyncio.run(run_experiment())
            except KeyboardInterrupt:
                print("User cancelled.")
                kill_tasks()
        case "report":
            # report()
            pass
