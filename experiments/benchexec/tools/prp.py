"""
                  -{ General Statistics }-

        FSAP Combination Count: 0
       Monotonicity violations: 0
             Successful states: 719 +/- 0
                       Replans: 0 +/- 0
                       Actions: 719 +/- 0
             Recorded Deadends: 16
            State-Action Pairs: 16
  Forbidden State-Action Pairs: 49
               Strongly Cyclic: True
                  Policy Score: 1
                     Succeeded: 1 / 1
 Depth limit (of 1000) reached: 0 / 1


                  -{ Timing Statistics }-

        Regression Computation: 0s
         Engine Initialization: 0s
                   Search Time: 0s
           Policy Construction: 0s
 Evaluating the policy quality: 10.27s
              Using the policy: 4.93s
          Just-in-case Repairs: 10.27s
                Simulator time: 0s
                    Total time: 10.27s



Strong cyclic plan found.
Peak memory: 5636 KB
"""

from benchexec.tools.template import BaseTool2
import benchexec.result as result


class Tool(BaseTool2):

    def __init__(self) -> None:
        super().__init__()
        self._output_dir = "./benchexec_output/prp"

    def executable(self, tool_locator):
        # this is the executable binary of the solver
        return tool_locator.find_executable("prp")

    def name(self):
        return "PRP"

    def program_files(self, executable):
        return self._program_files_from_executable(
            executable, self.REQUIRED_PATHS, parent_dir=True
        )

    def cmdline(self, executable, options, task, rlimits):
        """
        --jic-limit
        """
        options += ["--jic-limit", str(rlimits.cputime)]
        return [executable] + list(task.input_files) + options

    def determine_result(self, run):
        """
        @return: status of the solver output
        """
        status = result.RESULT_FALSE_PROP
        for line in run.output:
            # for prp
            if "Strong cyclic plan found" in line:
                status = result.RESULT_TRUE_PROP
            elif "plan found" in line:
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
        # Total time: 10.27s
        """
        for _l in output:
            if "Total time" in _l:
                return _l.split(":")[-1].strip().replace("s", "")

        return -1

    def _get_policy_size(self, output):
        """
        # Policy size: 3
        """
        for _l in output:
            if "Policy size" in _l:
                return _l.split(":")[-1].strip()

        return -1
