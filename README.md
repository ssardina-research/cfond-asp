# A Declarative Approach to Compact Controllers for FOND Planning via Answer Set Programming

A FOND planner based on Answer Set Programming, inspired by a synthesis between [FOND-SAT](https://github.com/tomsons22/FOND-SAT) and [PRP](https://github.com/QuMuLab/planner-for-relevant-policies) planners. 

The planner and its underlying technique were reported in the following paper:

* Nitin Yadav, Sebastian Sardiña: [A Declarative Approach to Compact Controllers for FOND Planning via Answer Set Programming](https://doi.org/10.3233/FAIA230593). ECAI 2023: 2818-2825


## Requirements

- Python 3.11 with dependencies as per `requirements.txt`. 
  - The listed Python packages may have other dependencies (e.g., `libxml2` and `libxslt` development packages).
- [Clingo](https://potassco.org/clingo/) ASP solver.

## File structure

- [`benchmarking/`](benchmarking/) contains scripts and FOND domains for benchmarking this planner
- [`src`/](src/) contains the python and ASP source files for the planner.

## Usage

The planner can be executed with the following command:

```shell
$ python src/python/main.py [options] fond_domain fond_problem
```

Use `-h` to get all options available.

The `main.py` script parses the input and solves the planning instance as follows:

1. Ground the planning planning instance and generate corresponding [SAS](https://www.fast-downward.org/TranslatorOutputFormat) file.
2. Translate the SAS file to a ASP file `instance.lp`.
3. Call Clingo with `instance.lp` and the chosen ASP planning solver model.

Resulting output files will be left in the corresponding output directory (`./output` by default), including Clingo output for each iteration (wrt controller size), SAS encoding and output, ASP instance used, and stat file.

For example to solve the `p03.pddl` problem from the `Acrobatics` domain:
```
$ python src/python/main.py benchmarking/problems/acrobatics/domain.pddl benchmarking/problems/acrobatics/p03.pddl

...
2024-01-12 15:04:30 nitin FondASP[195427] INFO Solution found for id /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/domain.pddl, /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/p03.pddl!
2024-01-12 15:04:30 nitin __main__[195427] INFO Time(s) taken:1.6477028469962534
```

### Clingo parameters

To pass specific argument to Clingo use `--clingo_args` as a quoted string. For example, to tell Clingo to use 4 threads:

```shell
$ python src/python/main.py benchmarking/problems/acrobatics/domain.pddl benchmarking/problems/acrobatics/p03.pddl  --clingo_args '-t 4'

...
2024-01-12 15:05:45 nitin FondASP[195707] INFO Solution found for id /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/domain.pddl, /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/p03.pddl!
2024-01-12 15:05:45 nitin __main__[195707] INFO Time(s) taken:1.3016068750002887
```

### Use backbone for minimum controller size estimation

To use _backbone_ size estimation (a lower bound on the size of the controller) to reduce the number of iterations, use `--use_backbone` option:

```
$ python src/python/main.py benchmarking/problems/acrobatics/domain.pddl benchmarking/problems/acrobatics/p03.pddl  --clingo_args '-t 4' --use_backbone True

...
2024-01-12 15:06:35 nitin FondASP[195939] INFO Solution found for id /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/domain.pddl, /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/p03.pddl!
2024-01-12 15:06:35 nitin __main__[195939] INFO Time(s) taken:1.2567479549907148
```

### Use domain knowledge

One can incorporate additional domain (control) knowledge in the planner by specifying additional ASP code, usually integrity constraints forbidding certain situations, and use option `--extra_constraints`.

For example, to tell the planner to completely _exclude_ action `jump` in the `Acrobatics` domain, we create a new file with the following ASP constraint:

```prolog
:- policy(State, Action), state(State), actionType("jump-over", Action).
```

If the file is called `acrobatics.lp`, one can then run the planner with option `--extra_constraints`:

```shell
$ python src/python/main.py benchmarking/problems/acrobatics/domain.pddl benchmarking/problems/acrobatics/p03.pddl  --clingo_args '-t 4' --use_backbone --extra_constraints ./acrobatics.lp

...
Solution found for id /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/domain.pddl, /home/nitin/Work/Software/cfond-asp/benchmarking/problems/acrobatics/p03.pddl!
2024-01-12 15:15:58 nitin __main__[198321] INFO Time(s) taken:0.9603760419995524
```

### Verification of controller

To _verify_ a strong-cyclic solution one can set the task to `verify` via option `--task`.

For example, to verify the solution for the `p03.pddl` problem from the `Acrobatics domain`:

```
$ python src/python/main.py benchmarking/problems/beam-walk/domain.pddl benchmarking/problems/beam-walk/p03.pddl --task verify

2024-01-12 14:45:31 nitin FondASP[192070] INFO Solution is sound? True
2024-01-12 14:45:31 nitin __main__[192070] INFO Time(s) taken:0.032270914001856
```

This will first translate Clingo output to a readable controller format (see the file `solution.out` in the output directory), and then check the controller found is indeed strong-cyclic.

Verification result will be left in file `verify.out`

## Benchmarking

The `benchmarking/` folder contains scripts to facilitate running benchmarks, possibly on a cluster or HPC. The scripts are sensitive to the current working directory and should be called from the root of this project.

The benchmarking system can run many problem instances using several solver configurations and using multiple CPU cores by running many instances simultaneously.

The folders under benchmarking are:

- `problems/`: FOND benchmarks.
- `code/`: This folder contains scripts to runs the problems and parse the output into CSV file.
- `configs/`: This folder contains example JSON configuration files to benchmark different planner settings.

The steps for benchmarking are:

1. Design experiment configuration and instance files.
2. Executing the benchmarks.

We now describe each of these steps in more detail.

### 1. Configuration & files

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

Under this configuration, instances under four scenarios will be run against two solver configurations named `asp1` and `asp2`. Limits on time and memory usage can also be specified.

### 2. Executing Benchmarks

To run the benchmark use the following command:

```Shell
$ python ./benchmarking/code/benchmark.py [options] instances_csv config_json
```

where `instances_csv` if the CSV file containing instances to solve and `config_json` is the JSON file configuring the experiments. Use `-h` to see all options available.

File `benchmarking/problems/instances.csv` contains _all_ problems available under `./benchmarking/problems` can be found:

```csv
scenario,domain,instance,output
triangle-tireworld,./benchmarking/problems/triangle-tireworld/domain.pddl,./benchmarking/problems/triangle-tireworld/p01.pddl,triangle-tireworld/p01
triangle-tireworld,./benchmarking/problems/triangle-tireworld/domain.pddl,./benchmarking/problems/triangle-tireworld/p02.pddl,triangle-tireworld/p02
triangle-tireworld,./benchmarking/problems/triangle-tireworld/domain.pddl,./benchmarking/problems/triangle-tireworld/p03.pddl,triangle-tireworld/p03
...
```

Note the path to each domain and problem file is relative to the root of the project. The output column specifies the folder where results for the particular output should be saved.

To solve _many_ instances at the same time, use the batch option `-n`. The default is to run two at the same time. Please note that the batch size option should be carefully set based on the number of threads configured for the planners (as each thread will take already one CPU core by itself).

For example:

```shell
$ python ./benchmarking/code/benchmark.py -n 4 --output output-bench  benchmarking/problems/instances_single.csv benchmarking/configs/config.json
```

The script will display a progress screen with the current instances being run and the total number of instances left.

It is recommended to run the benchmarking using a terminal multiplexer, like tmux.


### 3. **Generating CSVs from output.**

Finally, to export benchmarking results run the script under `report` mode:

```
$ python ./benchmarking/code/benchmark.py [options] instances.csv config.json --output <OUTPUT_DIR> --mode report
```

where `OUTPUT_DIR` is the location of output folder. Executing this will generate `report.csv` in the output directory.

```csv
domain,instance,planner,SAT,time,memory,timeout,memoryout,policysize
miner,p01,asp4,True,3.8785169249749742,294.44921875,0,0,18
miner,p01,asp1,True,4.386864872998558,284.40234375,0,0,18
miner,p02,asp4,True,3.09084887400968,247.86328125,0,0,15
miner,p02,asp1,True,3.511407638026867,263.8125,0,0,15
miner,p03,asp4,True,3.870103912020568,289.55859375,0,0,14
miner,p03,asp1,True,4.439991983002983,291.48828125,0,0,14
doors,p01,asp4,True,0.07492873800219968,165.1015625,0,0,5
doors,p01,asp1,True,0.08289377903565764,80.80859375,0,0,5
doors,p02,asp4,True,0.1647808289853856,128.55078125,0,0,7
doors,p02,asp1,True,0.1554079789784737,179.66015625,0,0,7
doors,p03,asp4,True,0.30981518898624927,180.0,0,0,9
doors,p03,asp1,True,0.32008328498341143,138.09765625,0,0,9
```