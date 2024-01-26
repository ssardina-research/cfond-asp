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

1. Ground the planning planning instance and generate corresponding [SAS](https://www.fast-downward.org/TranslatorOutputFormat) file (uses translator under [`src/translator-fond/`](src/translator-fond/)).
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

To pass specific argument to Clingo use `--clingo_args` as a quoted string. For example, to tell Clingo to use 4 threads and tell Clingo this is a single-shot task:

```shell
$ python src/python/main.py benchmarking/problems/acrobatics/domain.pddl benchmarking/problems/acrobatics/p03.pddl  --clingo_args '-t 4 --single-shot'

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

To _verify_ a strong-cyclic solution one can set the mode to `verify` via option `--mode`.

For example, to verify the solution for the `p03.pddl` problem from the `Acrobatics domain`:

```
$ python src/python/main.py benchmarking/problems/beam-walk/domain.pddl benchmarking/problems/beam-walk/p03.pddl --mode verify

2024-01-12 14:45:31 nitin FondASP[192070] INFO Solution is sound? True
2024-01-12 14:45:31 nitin __main__[192070] INFO Time(s) taken:0.032270914001856
```

This will first translate Clingo output to a readable controller format (see the file `solution.out` in the output directory), and then check the controller found is indeed strong-cyclic.

Verification result will be saved in file `verify.out`.

### Determinisation of instance

To only determinise the instance into the corresponding SAS encoding use the `determise` mode:

```shell
$ python src/python/main.py benchmarking/problems/beam-walk/domain.pddl benchmarking/problems/beam-walk/p03.pddl --mode determinise
```

This will just produce the corresponding SAS one-outcome determinised encoding of the problem instance, but it will not solve it.

The determinisation and SAS encoder is done by the code under [`src/translator-fond/`](src/translator-fond/) which has been borrowed from PRP codebase.

## Benchmarking

The `benchmarking/` folder contains scripts to facilitate running benchmarks, possibly on a cluster or HPC. The scripts are sensitive to the current working directory and should be called from the root of this project.

The benchmarking system can run many problem instances using several solver configurations and using multiple CPU cores by running many instances simultaneously.

The folders under benchmarking are:

- `problems/`: FOND benchmarks.
- `src/`: This folder contains scripts to runs the problems and parse the output into CSV file.
- `configs/`: This folder contains example JSON configuration files to benchmark different planner settings.

The steps for benchmarking are:

1. Design experiment configuration and instance files.
2. Run the benchmarking experiment.

We now describe each of these steps in more detail.

### 1. Configuration & instance files

First, define all the **instances available** in a CSV file. File `benchmarking/problems/instances.csv` contains _all_ problems available under `./benchmarking/problems`:

```csv
scenario,domain,instance,output
triangle-tireworld,./benchmarking/problems/triangle-tireworld/domain.pddl,./benchmarking/problems/triangle-tireworld/p01.pddl,triangle-tireworld/p01
triangle-tireworld,./benchmarking/problems/triangle-tireworld/domain.pddl,./benchmarking/problems/triangle-tireworld/p02.pddl,triangle-tireworld/p02
triangle-tireworld,./benchmarking/problems/triangle-tireworld/domain.pddl,./benchmarking/problems/triangle-tireworld/p03.pddl,triangle-tireworld/p03
...
...
...
```


Secondly, define the **experimental configuration** in a JSON file. This file will contain resource limits, scenarios to use, and solvers to run (with their specific configurations). Memory is in MB and time is in seconds. A sample config file is as follows:

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

Here, instances under four specific scenarios will be run against two solver configurations named `asp1` and `asp2`. Limits on time and memory usage can also be specified.

### 2. Run benchmarking experiment

To run the benchmark use the following command:

```Shell
$ python ./benchmarking/src/benchmark.py [options] instances_csv config_json
```

where `instances_csv` if the CSV file containing instances to solve and `config_json` is the JSON file configuring the experiments. Use `-h` to see all options available.

To solve _many_ instances at the same time, use the batch option `-n` (default is 2). Please note that the batch size option should be carefully set based on the number of threads configured for the planners (as each thread will take already one CPU core by itself).

It is recommended to run the benchmarking using a terminal multiplexer, like tmux.

For example:

```shell
$ python ./benchmarking/src/benchmark.py -n 4 --output output-bench  benchmarking/problems/instances_tiny.csv benchmarking/configs/config.json
```

The script will display a progress screen with the current instances being run and the total number of instances left.

It will also save the output of each run using folder structure `scenario/problem/solver`.

Once finished, a CSV file `report.csv` is also left in the output folder.

To only re-generate the report we can use the report script directly on the output folder:

```shell
$ python benchmarking/src/report.py output-bench
```

The report assumes the structure produced by the benchmarking scripts in the output, namely,  `scenario/problem/solver`.

