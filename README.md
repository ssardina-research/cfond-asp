# Compact FOND-ASP

Encoding of [FOND-SAT](https://github.com/ssardina-planning/FOND-SAT) approach in Answer Set Programming using [Clingo](https://potassco.org/clingo/).

This repo is hosted at https://github.com/ssardina-planning/fond-compact-asp

The link to the [GitHub Project](https://github.com/orgs/ssardina-planning/projects/1/).



## Requirements

- Python 3.10 with dependencies as per `requirements.txt`
- [FOND-SAT](https://github.com/ssardina-planning/FOND-SAT) planner.
- [Clingo](https://potassco.org/clingo/) ASP solver.
  - The ASP planner uses the determiniser from the FOND-SAT directory
- [PyPDDL-translator](https://github.com/ssardina-planning/pypddl-translator) parser and translator available as a Python package (see repo for instructions how to install as package).

## Usage

The `main.py` file takes just one argument: a *configuration file* with all the relevant details. A sample configuration file can be found in the configs folder. Example: 

```shell
$ python src/python/main.py ./configs/blocksworld.ini solve

2022-05-30 12:45:01 pacman-ai21---02 __main__[398236] INFO Read the config file configs/blocksworld.ini
2022-05-30 12:45:01 pacman-ai21---02 FondASP[398236] INFO Solving /mnt/ssardina-research/nitinseb/fond-compact-asp.git//benchmarking/problems/blocksworld-ipc08/domain.pddl with problem /mnt/ssardina-research/nitinseb/fond-compact-asp.git//benchmarking/problems/blocksworld-ipc08/p01.pddl using ASP.
2022-05-30 12:45:01 pacman-ai21---02 FondASP[398236] INFO  -Solving p01 with numStates=2.
2022-05-30 12:45:01 pacman-ai21---02 FondASP[398236] INFO  -Solving p01 with numStates=3.
2022-05-30 12:45:02 pacman-ai21---02 FondASP[398236] INFO  -Solving p01 with numStates=4.
2022-05-30 12:45:02 pacman-ai21---02 FondASP[398236] INFO  -Solving p01 with numStates=5.
2022-05-30 12:45:03 pacman-ai21---02 FondASP[398236] INFO  -Solving p01 with numStates=6.
2022-05-30 12:45:04 pacman-ai21---02 FondASP[398236] INFO  -Solving p01 with numStates=7.
2022-05-30 12:45:05 pacman-ai21---02 FondASP[398236] INFO  -Solving p01 with numStates=8.
2022-05-30 12:45:06 pacman-ai21---02 FondASP[398236] INFO Solution found for id p01!
```

Resulting files will be left in the corresponding output directory, as per configuration (see below).

The config file allows to configure the paths of the various needed systems based on where the software is running (e.g., `work` or `home`), for example:

```ini
[fond]
id = p01
time_limit = 0
location = work
scenario = blocksworld-ipc08
determiniser = prp
problem = ${scenario}/p01.pddl
domain = ${scenario}/domain.pddl
output = ${scenario}/${id}

[work]
root = ~/Work/Software/fond-compact-asp
problems = ${root}/benchmarking/problems
output_dir = ${root}/output
clingo = clingo
fondsat = ~/Tools/planners/FOND-SAT
prp_translate = ${fondsat}/src/translate/translate.py
fast_downward = ~/Tools/planners/fd/fast-downward.py
controller_model = ${root}/src/asp/controller.lp

[home]
root = ~/Work/Software/FondASP
problems = ${root}/benchmarking/problems
output_dir = ${root}/output
clingo = clingo
fondsat = ~/Tools/Planners/FOND-SAT
prp_translate = ${fondsat}/src/translate/translate.py
controller_model = ${root}/src/asp/controller.lp


[controller]
max_states = 100

[clingo]
num_threads = 1
ref = opt-1
args = --stats -t 1 --sat-p=2 --trans-ext=integ --eq=3 --reverse-arcs=2 --shuffle=1
```

This configuraiton file includes two location options, `home` and `work`, and the location is set to work (under `[fond]` section).

The various elements in the config file are:

- `fond`:
  - `id`: Name or identification of the instance. This is used to correctly store the generated output files (see output).
  - `time_limit`: A time limit in seconds for each iteration (`0` = no time limit).
  - `location`: Location to use. For example if location is `work`, paths from segment `[work]` will be used.
  - `scenario`: name of the folder where problem and domain files are located (e.g., `acrobatics`).
  - `determiniser`: `prp` or `fd`.
  - `problem`: relative path to the problem PDDL file.
  - `domain`: relative path to the domain PDDL file.
  - `output`: relative path of the output folder within the `output_dir` folder as per location section.
- Location paths (e.g., `[work]` and `[home]`):
  - `root`: location of the root of this repository.
  - `problems`: folder where all the problems are stored.
  - `output_dir`: location of the output directory where output from the solver will be stored.
  - `clingo`: path to clingo. If clingo is in system path then a full path can be omitted.
  - `fondsat`: path to the root of FOND-SAT system.
  - `prp_translate`: path to `translate.py` from PRP planner.
  - `controller_model`: path to the controller model to solve FOND via ASP
- `clingo`:
  - `num_threads`: number of threads for Clingo solver.
  - `ref`: A reference for this clingo configuration
  - `args`: Arguments to clingo solver
- `controller`: 
  - `max_states`: Maximum number of states to try.

The `main.py` script will parse the config file and solve the planning instance. The script will first ground the planning instance to create a SAS file. Then it will translate the SAS file to a file `instance.lp`. Finally, the script will call clingo with `instance.lp` and `controller.lp`.


### Verification of controller

To verify the solution one can pass the `verify` argument. 

For example: 

```shell
python src/python/main.py ./configs/blocksworld.ini verify
2022-05-30 12:56:09 pacman-ai21---02 __main__[398596] INFO Read the config file ./configs/blocksworld.ini
2022-05-30 12:56:09 pacman-ai21---02 FondASP[398596] INFO Solution is sound? True
```

This will first translate clingo output to a readable controller format (see the file `solution.out` in the output directory), and then check if the solution is strong cyclic.


## Benchmarking

The `benchmarking/` folder contains scripts to facilitate running benchmarks on an HPC. The scripts are sensitive to the current working directory and should be called from the root of this project.

The folders under benchmarking are:

- `problems/`: FOND benchmarks from FOND-SAT repository.
- `scripts/`: This folder contains scripts to generate configurations, runs the problems and parse the output into csv.
- `metaconfigs/`: This folder contains metaconfigs, one config per domain (e.g., `acrobatics`), from which configs from each instance will be generated.
- `configs/`: Folder where generated configs will be saved. 

The steps include:

1. Generating configurations from metaconfigs. 
2. Generating scripts to run instances in each scenario one-by-one, and scripts to run on HPC (e.g., slurm scripts). 
3. Process the outputs and create CSV files for analysis.

We now describe each of these steps in more detail.

### 1. **Generate configs.**

 1. Open `benchmarking/scripts/generate/generate_configs.py` and update the relevant variables. For example setting `location = "spartan"` will set paths according to [Spartan HPC](https://dashboard.hpc.unimelb.edu.au/).
 2. Update various Clingo and FOND-SAT configs (e.g., number of threads, configuration, reference, etc).
 3. Execute:
    
    ```shell
    $ python benchmarking/scripts/generate/generate_configs.py benchmarking/metaconfigs <solver>
    ```
    where `<solver>` is either `asp` or `fondsat`. 
    
    **Note: The files should be generated in the system where the system will run.**
 4. Check the configs folder to ensure config files have been generated.
   
### 2. **Executing Benchmarks.**

* Executing individual domain benchmarks.
   1. To execute ASP planner: 
   
   ```shell
   $ python benchmarking/scripts/execute/asp_benchmarks.py benchmarking/configs/<domain>/<asp-ref>
   ``` 
   where `<domain>` is one of the planning domains (e.g., `acrobatics`) and `<asp-ref>` is the reference to the subfolder where solver's config files are located.
   2. To execute FOND-SAT planner: 
   
   ```shell
   $ python benchmarking/scripts/execute/fondsat_benchmarks.py benchmarking/configs/<domain>/<fondsat-ref>
   ``` 
   where `<domain>` is one of the planning domains (e.g., `acrobatics`), and `<fondsat-ref>` is the reference to the subfolder where solver's config files are located.
* Executing benchmarks on slurm-based HPC.
   1. Open `benchmarking/scripts/generate/generate_hpc.py` and update relevant sbatch parameters.
   2. Execute: 
   
      ```shell
      $ python benchmarking/scripts/generate/generate_hpc.py benchmarking/configs slurm
      ```
      
   3. Check slurm scripts have been generated in the `benchmarking/hpc/slurm` folder.
   4. Execute: 
   
      ```shell
      $ <asp-ref>/<asp-ref>-sched-asp.sh
      $ <fondsat-ref>/<fondsat-ref>-sched-fondsat.sh
      ``` 
       in the slurm folder to schedule execution of the benchmarks.
* Executing benchmarks on native linux.
   1. Execute: 
   
      ```shell
      $ python benchmarking/scripts/generate/generate_hpc.py benchmarking/configs bash
      ```
   2. Check bash scripts have been generated in the `benchmarking/hpc/bash` folder.
   3. Execute the benchmarks by running the relevant scripts. There is no automatic scheduling hence scripts need to be scheduled manually.

### 3. **Generating CSVs from output.**
   
   Execute:
   
   ```shell
   $ python benchmarking/scripts/process/process_output.py <OUTPUT_DIR> <CSV_DIR>
   ``` 
   where `OUTPUT_DIR` is the location of output folder and `CSV_DIR` is the directory where csv's should be stored.

Two CSV files will be produced:

1. `final.csv`: This CSV file will contain the total times (solving and    grounding) for instances that were solved by all solvers
2. `interim.csv`: This CSV file will contain times for different iterations of instances for each solver.