"""
This script reasons on actions to find pairs such that they undo the effect of each other.
"""
import logging
import coloredlogs
from cfondasp.utils.helper_sas import organize_actions
from cfondasp.utils.translators import parse_sas


def reason(sas_file: str):
    initial_state, goal_state, actions, variables, mutexs = parse_sas(sas_file)
    det_actions, nd_actions = organize_actions(actions)


def _get_logger() -> logging.Logger:
    logger = logging.getLogger("UndoReasoner")
    coloredlogs.install(level='DEBUG')
    return logger


if __name__ == "__main__":
    sas_file = "./output/islands/asp-opt-1/output.sas"
    reason(sas_file)
