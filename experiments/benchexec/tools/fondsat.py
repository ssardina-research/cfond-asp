"""
SAT
Done solver. Round time: 0.158703
Cumulated solver time: 0.15870262496173382
PLANFOUND!
Number of controller states: 3
Elapsed total time (s): 1.656025
Elapsed initialisation time (s): 1.1450068338308483
Elapsed grounding time (s): 0.2957278750836849
Elapsed grounding time (s): [0.2957278750836849]
Elapsed solver time (s): 0.158703
Elapsed solver time (s): [0.15870262496173382]
Elapsed result output time (s): 0
Elapsed result output time (s): []
Looking for strong plans: False
Fair actions: True
Done
"""

from benchexec.tools.template import BaseTool2
import benchexec.result as result

class Tool(BaseTool2):

    def __init__(self) -> None:
        super().__init__()
        self._output_dir = "./benchexec_output/fondsat"

    def executable(self, tool_locator):
        return tool_locator.find_executable("fondsat")

    def name(self):
        return "Fondsat"

    def program_files(self, executable):
        return self._program_files_from_executable(
            executable, self.REQUIRED_PATHS, parent_dir=True
        )

    def cmdline(self, executable, options, task, rlimits):
        """
        ./src/fondsat ./F-domains/zenotravel/domain.pddl ./F-domains/zenotravel/p01.pddl --solver glucose --time-limit 10000 --end 100         
        """
        options += ["--time-limit", str(rlimits.cputime)]
        return [executable] + options + list(task.input_files) ["--show-policy"]

    def determine_result(self, run):
        """
        @return: status of the solver output
        """
        status = result.RESULT_FALSE_PROP
        for line in run.output:
            # for fondsat
            if "PLANFOUND!" in line:
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
        # Elapsed total time (s): 1.656025
        """
        for _l in output:
            if "Elapsed total time" in _l:
                return _l.split(":")[-1].strip()

        return -1


    def _get_policy_size(self, output):
        """
        # Number of controller states: 3
        """
        for _l in output:
            if "Number of controller states" in _l:
                return _l.split(":")[-1].strip()
            
        return -1
