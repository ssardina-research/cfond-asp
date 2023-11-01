import asyncio
import logging
import subprocess
from asyncio.subprocess import Process
from typing import List
import coloredlogs
import sys

logger: logging.Logger = None

def _get_logger():
    global logger

    if not logger:    
        # set logger
        logger = logging.getLogger("ClingoExecutor")
        coloredlogs.install(level='INFO', logger=logger)

    return logger

def execute_asp(executable: str, args: List[str], input_files: List[str], output_dir: str, output_file: str) -> bool:
    """
    Execute the fast-downward translator on the given domain and problem to generate a SAS output
    :param executable: path to fast-downward
    :param args: arguments to clingo
    :param input_files: list of input files to clingo
    :param output_dir: path where clingo will be run
    :param output_file: path to the output file
    :return: If a solution is found, If the process timed out
    """
    executable_list = [executable] + input_files + args
    logger = _get_logger()
    try:
        process = subprocess.Popen(executable_list, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        stdout, stderr = process.communicate()

        # check for any errors
        if stderr:
            _error = stderr.decode()
            logger.error(_error)
            sys.exit(1)

        # save output
        with open(output_file, "w") as f:
            f.write(stdout.decode())

        return is_satisfiable(output_file)
    except Exception as e:
        print("ERROR while executing Clingo.")
        print(e)


async def execute_asp_async(executable: str, args: List[str], input_files: List[str], output_dir: str, output_file: str) -> (bool, bool):
    """
    Execute the fast-downward translator on the given domain and problem to generate a SAS output
    :param executable: path to fast-downward
    :param args: arguments to clingo
    :param input_files: list of input files to clingo
    :param output_dir: path where clingo will be run
    :param output_file: path to the output file
    :return: If a solution is found, If the process timed out
    """
    program = [executable] + input_files + args

    process: Process = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE, cwd=output_dir)
    await process.wait()

    # read output.
    data = await process.stdout.read()
    line = data.decode('ascii').rstrip()

    # save output
    with open(output_file, "w") as f:
        f.write(line)

    return is_satisfiable(output_file)


def is_satisfiable(clingo_output: str):
    with open(clingo_output) as f:
        info = f.readlines()

    for _line in info:
        if "UNSATISFIABLE" in _line:
            return False
        elif "SATISFIABLE" in _line:
            return True
