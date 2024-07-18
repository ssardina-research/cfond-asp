"""
Tool for executing Paladinus FOND solver. 
The output of paladinus on solving is:
Total Memory (GB) = 0.0027516186237335205

INITIAL IS PROVEN!

Result: Policy successfully found.

Time needed for preprocess (Parsing, PDBs, ...):    0.006 seconds.
Time needed for search:                             0.005 seconds.
Time needed:                                        0.011 seconds.
Total Garbage Collections: 1
Total Garbage Collection Time: 0 seconds.

# Number Iterations         = 3

# Total Nodes               = 4
# Number of Expansions      = 11
# Number of Node Expansions = 8
# Policy Size               = 3
# Total Time                = 0.011 seconds.
"""

from benchexec.tools.template import BaseTool2
import benchexec.result as result


class Tool(BaseTool2):

    def __init__(self) -> None:
        super().__init__()
        self._output_dir = "./benchexec_output/paladinus"

    def executable(self, tool_locator):
        return tool_locator.find_executable("paladinus")

    def name(self):
        return "Paladinus"

    def program_files(self, executable):
        return self._program_files_from_executable(
            executable, self.REQUIRED_PATHS, parent_dir=True
        )

    def cmdline(self, executable, options, task, rlimits):
        options += ["-timeout", str(rlimits.cputime), "-exportPolicy", f"{self._output_dir}/policy.out"]
        return [executable] + options + list(task.input_files)

    def determine_result(self, run):
        """
        @return: status of the solver output
        """
        status = result.RESULT_FALSE_PROP
        for line in run.output:
            # for paladinus
            if "Result: Policy successfully found" in line:
                status = result.RESULT_TRUE_PROP

        return status

    def get_value_from_output(self, output, identifier):
        if identifier.lower() == "policy_size":
            return self._get_policy_size(output)
        elif identifier.lower() == "planner_time":
            solve_time = self._get_solve_time(output)
            return solve_time

    def _get_solve_time(self, output):
        """
        # Total Time = 0.011 seconds.
        """
        for _l in output:
            if "Total Time" in _l:
                return _l.split("=")[-1].strip().split()[0]

        return -1


    def _get_policy_size(self, output):
        """
        # Policy Size = 3
        """
        for _l in output:
            if "Policy Size" in _l:
                return _l.split("=")[-1].strip()
            
        return -1
