import asyncio
import os
import signal
import traceback
import psutil

from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn, MofNCompleteColumn
from rich.live import Live
from rich.table import Table, box
from rich.layout import Layout
from task import Task
from datetime import datetime
from rich.console import Console
MB_CONVERSION = 1024 * 1024

class Monitor(object):

    def __init__(self, total: int) -> None:
        self.total: int = total
        self.layout: Layout = Layout()
        self.progress = None
        self.total_progress = None
        self.active_tasks = {}
        self.finished_count = 0
        self._make_layout()
        self.stop = False
        self.console = Console()

    def _make_layout(self):
        self.layout.split_column(
            Layout(name="active"),
            Layout(name="status")
        )

        self.progress =  Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            SpinnerColumn())

        self.total_progress = self.progress.add_task("[green]Finished: ", total=self.total)
        self.layout["status"].update(self.progress)

        table = Table(title="Active instances.", box=box.HORIZONTALS)
        table.add_column("id")
        table.add_column("pid")
        table.add_column("solver")
        table.add_column("time")
        table.add_column("memory")
        self.layout["active"].update(table)

    def update(self, active_tasks, finished_count):
        self.active_tasks = active_tasks
        self.finished_count = finished_count

    def start(self):
        try:
            asyncio.gather(self._run())
        except KeyboardInterrupt:
            pass
        except asyncio.CancelledError:
            pass

    def get_memory(self, task: Task):
        try:
            process = psutil.Process(task.pid)
            memory = 0   # we don't want to consider the memory of the root shell process
            for child in process.children(recursive=True):
                memory += child.memory_info().rss
        except psutil.NoSuchProcess:    # process has finished already
            memory = 0

        # set the max memory used by this task
        memory_mb = memory/MB_CONVERSION
        if task.memory < memory_mb:
            task.memory = memory_mb
            
        return memory_mb
    
    def check_memory(self, task: Task):
        if task.memory > task.memory_limit:
            task.store_memory(exceeded=True)
            task.kill()

    async def _run(self):
        try:
            while not self.stop:

                table = Table(title="Active instances.", box=box.HORIZONTALS)
                table.add_column("id")
                table.add_column("pid")
                table.add_column("solver")
                table.add_column("scenario")
                table.add_column("problem")
                table.add_column(f"time (max {Task.time_limit}s)")
                table.add_column(f"memory (max {Task.memory_limit}M)")
                table.add_column("consumer")

                for _id, _task in self.active_tasks.items():
                    _time = (datetime.now() - _task.start_time).total_seconds()
                    prefix = ""
                    if _time/_task.time_limit > 0.8:
                        prefix = "[#FFA500]"
                    time_str = f"{prefix}{_time:0.3f}"

                    _memory = self.get_memory(_task)
                    prefix = ""
                    if _memory/_task.memory_limit > 0.8:
                        prefix = "[#FFA500]"
                    memory_str = f"{prefix}{_memory:0.3f}"

                    table.add_row(str(_task.id), str(_task.pid), _task.solver, _task.scenario, _task.problem, time_str, memory_str, _task.queue)
                    self.check_memory(_task)

                with Live(self.layout, console=self.console, auto_refresh=False):
                    self.progress.update(self.total_progress, completed=self.finished_count)
                    self.layout["status"].update(self.progress)
                    self.layout["active"].update(table)

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            traceback.print_exc()

