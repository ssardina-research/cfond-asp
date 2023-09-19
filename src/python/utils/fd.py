import logging
import subprocess
import sys
from typing import List

import coloredlogs


def compute_weak_plan(input_files: List[str], fd_path: str, cwd: str):
    """
    Run the fast downward planner on the determinised domain and instance, and extract the plan length from its output.
    :param input_files: input files to fd
    :param fd_path: path to fast downward
    :param cwd: directory where fd should run
    :return:

    Note: Prp runs fd with --heuristic "h=ff(cost_type=1)" --search "lazy_greedy([h],preferred=[h])"
    """
    _logger: logging.Logger = _get_logger()
    executable_list = [fd_path] + input_files + ['--evaluator', "hff=ff()", '--evaluator', "hcea=cea()"] + ['--search', "lazy_greedy([hff, hcea], preferred=[hff, hcea])"]
    try:
        process = subprocess.Popen(executable_list, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        stdout, stderr = process.communicate()
    except Exception as e:
        _logger.error(e)

    return


def _get_logger() -> logging.Logger:
    logger = logging.getLogger("FDHelper")
    coloredlogs.install(level='INFO')
    return logger
