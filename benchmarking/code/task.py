from enum import Enum, auto
import os
import signal

class TaskStatus(Enum):
    NOT_STARTED = auto()
    FINISHED = auto(),
    RUNNING = auto(),
    ERROR = auto()


class Task(object):
    memory_limit: int = 0
    time_limit: int = 0
    def __init__(self, id, scenario, cmd, solver, output_path) -> None:
        self.id: str = id
        self.scenario: str = scenario
        self.cmd: str = cmd
        self.start_time = None
        self.pid = 0
        self.output_path = output_path
        self.memory_exceeded = False
        self.memory = 0
        self.solver: str = solver
        self.status: TaskStatus = TaskStatus.NOT_STARTED

    def store_memory(self, exceeded=False):
        self.memory_exceeded = exceeded
        with open(os.path.join(self.output_path, "memory.out"), "w+") as f:
            f.write(f"Memory limit: {self.memory_limit}{os.linesep}")
            f.write(f"Memory used:{self.memory}{os.linesep}")
            f.write(f"Memory exceeded: {exceeded}{os.linesep}")

    def kill(self):
        try:
            os.killpg(os.getpgid(self.pid), signal.SIGTERM)  
        except ProcessLookupError:
            pass # already finished?