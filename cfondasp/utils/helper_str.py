from typing import List


def get_indices_between(info: List[str] | str, start: str, end: str) -> List[tuple[int, int]]:
    """
    A helper function to return tuples of start-stop indices corresponding to the start-stop strings in a file.
    For example, given information of a SAS file and strings "begin_variable", "end-variable" the function will return the indices corresponding to these strings
    :param info: Information from the relevant file
    :param start: start string
    :param end: end string
    :return: list of tuples, where each tuple is a pair corresponding to indices of the start and stop strings in the given list of strings.

    Note: we assume that that SAS file is consistent, that is, each start string is associated with a corresponding end string.
    """
    start_indices = [i for i, x in enumerate(info) if x.strip().startswith(start)]
    end_indices = [i for i, x in enumerate(info) if x.strip().startswith(end)]

    return list(zip(start_indices, end_indices))
