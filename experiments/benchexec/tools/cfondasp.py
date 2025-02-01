"""
This is the tool for benchexec (https://github.com/sosy-lab/benchexec) 
for CFOND-ASP planner (https://github.com/ssardina-research/cfond-asp)
"""
from benchexec.tools.template import BaseTool2
import benchexec.result as result

class Tool(BaseTool2):

    def __init__(self) -> None:
        super().__init__()
        self._output_dir = "./benchexec_output/cfondasp"

    def executable(self, tool_locator):
        # this is the executable binary of the solver
        return tool_locator.find_executable("cfond-asp")

    def name(self):
        return "CFondASP"

    def program_files(self, executable):
        return self._program_files_from_executable(
            executable, self.REQUIRED_PATHS, parent_dir=True
        )

    def cmdline(self, executable, options, task, rlimits):
        """
        Example:
        
        cfond-asp ./benchmarks/acrobatics/domain.pddl ./benchmarks/acrobatics/p03.pddl --model fondsat --use-backbone --filter_undo --clingo-args "-t 2" --output ./output 
        """
        use_control_kb = False
        new_options = []
        for option in options:
            if "use_ckb" in option:
                use_control_kb = True
            else:
                new_options.append(option)
            
        if use_control_kb and "kb" in task.options:
            new_options += ["--domain-kb", task.options["kb"]]
        new_options += ["--timeout", str(rlimits.cputime)]
        # new_options += ["--translator-path", str(rlimits.cputime)]
        return [executable] + new_options + list(task.input_files) + ["--output", f"{self._output_dir}/{task.options['output']}"]

    def determine_result(self, run):
        """
        @return: status of the solver output
        """
        status = result.RESULT_FALSE_PROP
        for line in run.output:
            # for fondasp
            if "Solution found" in line:
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
        # Time taken: 2.087560167070478
        """
        for _l in output:
            if "Time taken:" in _l:
                return _l.split(":")[-1].strip()

        return -1


    def _get_policy_size(self, output):
        """
        #  Number of states in controller: 16
        """
        for _l in output:
            if "Number of states in controller" in _l:
                return _l.split(":")[-1].strip()
            
        return -1
