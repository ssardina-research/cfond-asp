# A Declarative Approach to Compact Controllers for FOND Planning via Answer Set Programming

A FOND planner based on Answer Set Programming. 
The corresponding paper can be found [here](https://doi.org/10.3233/FAIA230593).


## Requirements

- Python 3.11 with dependencies as per `requirements.txt`. The listed python packages may have other dependencies (e.g., libxml2 and libxslt development packages).
- [Clingo](https://potassco.org/clingo/) ASP solver.

## File structure
- `benchmarking` contains scripts and FOND domains for benchmarking this planner
- `src` contains the python and ASP source files for the planner. 

## Usage

The planner can be executed with the following command:
```shell
$ python src/python/main.py [options] fond_domain fond_problem
``` 

Other options include:
```
  -h, --help            show this help message and exit
  --max_states MAX_STATES
                        Maximum number of controller states
  --what_to_do {solve,verify,determinise}
                        Functionality of the system to execute. Currently, verification only works for strong cyclic plans.
  --solution_type {strong,strong-cyclic}
                        Should the planner look for strong or strong cyclic solutions
  --timeout TIMEOUT     timeout for solving the problem (in seconds).
  --model {fondsat,regression}
                        ASP model to use for FOND (only relevant for strong cyclic solutions)
  --clingo_args CLINGO_ARGS
                        Arguments to Clingo
  --extra_constraints EXTRA_CONSTRAINTS
                        Addtional asp constraints (as input file to clingo)
  --filter_undo FILTER_UNDO
                        Filter undo actions from policy consideration.
  --use_backbone USE_BACKBONE
                        Use backbone size for minimum controller size estimation
  --domain_kb {triangle-tireworld,miner,acrobatics,spikytireworld}
                        Add pre-defined domain knowledge.
  --output OUTPUT       location of output folder
```

Resulting files will be left in the corresponding output directory.


The `main.py` script will parse the input and solve the planning instance. The script will first ground the planning instance to create a SAS file. Then it will translate the SAS file to a file `instance.lp`. Finally, the script will call clingo with `instance.lp` and  the chosen ASP model.

For example to solve the `p03.pddl` problem from the `Acrobatics` domain one can execute:
```
$ python src/python/main.py benchmarking/problems/acrobatics/domain.pddl benchmarking/problems/acrobatics/p03.pddl

...
2024-01-12 15:04:30 nitin FondASP[195427] INFO Solution found for id /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/domain.pddl, /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/p03.pddl!
2024-01-12 15:04:30 nitin __main__[195427] INFO Time(s) taken:1.6477028469962534
```

### Clingo parameters
One can pass additional clingo arguments using `--clingo_args`. For example, the command below runs the planner with 4 threads.

```
$ python src/python/main.py benchmarking/problems/acrobatics/domain.pddl benchmarking/problems/acrobatics/p03.pddl  --clingo_args '-t 4'

...
2024-01-12 15:05:45 nitin FondASP[195707] INFO Solution found for id /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/domain.pddl, /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/p03.pddl!
2024-01-12 15:05:45 nitin __main__[195707] INFO Time(s) taken:1.3016068750002887
```

### Using backbone for minimum size estimation
One can use backbone size estimation to reduce the number of iterations by using the `--use_backbone` argument. 

```
$ python src/python/main.py benchmarking/problems/acrobatics/domain.pddl benchmarking/problems/acrobatics/p03.pddl  --clingo_args '-t 4' --use_backbone True

...
2024-01-12 15:06:35 nitin FondASP[195939] INFO Solution found for id /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/domain.pddl, /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/p03.pddl!
2024-01-12 15:06:35 nitin __main__[195939] INFO Time(s) taken:1.2567479549907148
```

### Incorporating domain knowledge
One can easily incorporate additional domain knowledge in the planner. For example, suppose a domain expert asks to exclude the action `jump` in the `Acrobatics` domain. To do this, one needs to create a new file with this constraint encoded in ASP. An example is shown below:

```ASP
:- policy(State, Action), state(State), actionType("jump-over", Action). 
```

Save this in a file called `acrobatics.lp`. One can then use the following command to provide this extra constraint.

```
$ python src/python/main.py benchmarking/problems/acrobatics/domain.pddl benchmarking/problems/acrobatics/p03.pddl  --clingo_args '-t 4' --use_backbone True --extra_constraints ./acrobatics.lp

...
Solution found for id /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/domain.pddl, /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/p03.pddl!
2024-01-12 15:15:58 nitin __main__[198321] INFO Time(s) taken:0.9603760419995524
```

### Verification of controller

To verify a strong-cyclic solution one can use the `verify` argument. 

For example to verify the solution for the `p03.pddl` problem from the `Acrobatics domain` one can execute: 

```
$ python src/python/main.py benchmarking/problems/beam-walk/domain.pddl benchmarking/problems/beam-walk/p03.pddl --what_to_do verify

2024-01-12 14:45:31 nitin FondASP[192070] INFO Solution is sound? True
2024-01-12 14:45:31 nitin __main__[192070] INFO Time(s) taken:0.032270914001856
```

This will first translate clingo output to a readable controller format (see the file `solution.out` in the output directory), and then check if the solution is strong cyclic.


## Benchmarking

The `benchmarking/` folder contains scripts to facilitate running benchmarks on an HPC. The scripts are sensitive to the current working directory and should be called from the root of this project.

The folders under benchmarking are:

- `problems/`: FOND benchmarks.
- `code/`: This folder contains scripts to runs the problems and parse the output into csv.
- `configs/`: This folder contains example json configs to benchmark different planner settings.


The steps include:

1. Updating the config file
2. Executing the benchmarks
3. Export the report

We now describe each of these steps in more detail.

### 1. **Config file**

The config file specifies benchmark parameters such as the time (in seconds) and memory (in MB) limits, the planning domains to test on, and the configurations of the planner. A sample config file is shown below.

```JSON
{
 "time_limit": 14400,  
 "memory_limit": 4096,
 "run": ["asp1", "asp4"],
 "scenarios": ["miner", "doors", "islands", "spiky-tireworld"],
 "solvers": {
    "asp1": {
        "args": "--clingo_args '-t 1'"
    },
    "asp4": {
        "args": "--clingo_args '-t 4'"
    }
 }
}
```
   
### 2. **Executing Benchmarks.**

To run the benchmark use the following command:
```Shell
$ python ./benchmarking/code/benchmark.py [options] instances.csv config.json
```

Various options for the benchmarking script are as follows:

```
positional arguments:
  csv                   Path to csv file containing information about instances.
  config                Path to config file containing information about solvers.

options:
  -h, --help            show this help message and exit
  --output OUTPUT       Path to root output directory where all solving information will be stored.
  --mode {run,report}   Functionality of the system to execute run.
  -n BATCH_SIZE, --num BATCH_SIZE
                        Number of instances to solve in parallel (default 2)
  --skip                If solved instances should be skipped
```

An `instances.csv` containing information about all instances in the problem folder can be found in `./benchmarking/problems`. Please note that the batch size option should be carefully set based on the number of threads configured for the planners.

### 3. **Generating CSVs from output.**
   
   To export benchmarking results execute:
   
   ```
   $ python ./benchmarking/code/benchmark.py [options] instances.csv config.json --output <OUTPUT_DIR> --mode report
   ``` 
   where `OUTPUT_DIR` is the location of output folder.
