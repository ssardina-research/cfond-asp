import asyncio
import logging
import subprocess
from asyncio.subprocess import Process
from typing import List
import coloredlogs
import sys
from utils.system_utils import get_now

logger: logging.Logger = None
ERROR_IGNORE = ["mutexgroup"]


def _should_ignore_error(error) -> bool:
    for _i in ERROR_IGNORE:
        if _i in error.lower():
            return True
    return False

def _get_logger():
    global logger

    if not logger:
        # set logger
        logger = logging.getLogger("ClingoExecutor")
        coloredlogs.install(level='INFO', logger=logger)

    return logger

def set_logger(l):
    global logger
    logger = l



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
    cmd_executable = ' '.join(executable_list)
    logger = _get_logger()
    try:
        file_out = open(output_file, "w")
        time_start = get_now()
        file_out.write(f"Time start: {time_start}\n\n")
        file_out.write(cmd_executable)
        file_out.write("\n")

        process = subprocess.Popen(executable_list, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        stdout, stderr = process.communicate()
        returncode = process.returncode
        time_end = get_now()

        # check for any errors 
        # (SS: not used anymore as we send stderr to stdout!)
        # if stderr:
        #     _error = stderr.decode()
        #     if _should_ignore_error(_error):
        #         logger.debug(_error)
        #     else:
        #         logger.error(_error)
        #         sys.exit(1)

        # save output
        file_out.write(stdout.decode())

        file_out.write("\n\n")
        file_out.write(f"Time end: {time_end}\n")
        file_out.write(f"Clingo return code: {returncode}\n")
        file_out.close()

        return is_satisfiable(output_file)
    except Exception as e:
        logger.error(f"ERROR while executing Clingo: {e}")
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
    executable_list = [executable] + input_files + args
    cmd_executable = ' '.join(executable_list)

    file_out = open(output_file, "w")
    time_start = get_now()
    file_out.write(f"Time start: {time_start}\n\n")
    file_out.write(cmd_executable)
    file_out.write("\n")

    process: Process = await asyncio.create_subprocess_exec(*executable_list, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, cwd=output_dir)
    await process.wait()

    returncode = process.returncode
    time_end = get_now()

    # read output.
    data = await process.stdout.read()
    line = data.decode('ascii').rstrip()

    # save output
    file_out.write(line)
    file_out.write("\n\n")
    file_out.write(f"Time end: {time_end}\n")
    file_out.write(f"Clingo return code: {returncode}\n")
    file_out.close()

    return is_satisfiable(output_file)


def is_satisfiable(clingo_output: str):
    with open(clingo_output) as f:
        info = f.readlines()

    for _line in info:
        if "UNSATISFIABLE" in _line:
            return False
        elif "SATISFIABLE" in _line:
            return True
