# Benchmarking CFOND-ASP

The [`benchmarking/`](benchmarking/) folder contains scripts to facilitate running benchmarks, possibly on a cluster or HPC. The scripts are sensitive to the current working directory and should be called from the root of this project.

The benchmarking system can run many problem instances using several solver configurations and using multiple CPU cores by running many instances simultaneously.

The folders under [`benchmarking/`](benchmarking/) are:

- `problems/`: FOND benchmarks.
- `src/`: This folder contains scripts to runs the problems and parse the output into CSV file.
- `configs/`: This folder contains example JSON configuration files to benchmark different planner settings.

The steps for benchmarking are:

1. Build instance CSV file containing all the problem instances that are available to test on.
2. Build experiment configuration file, stating the settings of the experiment.
3. Write domain dependent API parsing functions in file [`benchmarking/src/domain_spec.py`](benchmarking/src/domain_spec.py)
4. Run the benchmarking experiment.

We now describe each of these steps in more detail.

## 1. Instance CSV file

The first thing is to have a CSV file listing all the problem instances that are _available_ to be used in an experiment.

The set of instances can be organized on two levels. The first level specifies the **scenario**, and the second specifies the specific **id** of the instance. A scenario, such as Blockworlds, will usually have several instances, one with a unique id.

The first two columns of the CSV should specify the scenario and the instance id. These are mandatory for any benchmarking framework.

Then, for the case of FOND planning, the remaining two columns will specify the folder of the planning domain and that of the problem instance. For example:

```csv
scenario,id,domain,problem
triangle-tireworld,p01,./benchmarking/problems/triangle-tireworld/domain.pddl,./benchmarking/problems/triangle-tireworld/p01.pddl
triangle-tireworld,p02,./benchmarking/problems/triangle-tireworld/domain.pddl,./benchmarking/problems/triangle-tireworld/p02.pddl
triangle-tireworld,p03,./benchmarking/problems/triangle-tireworld/domain.pddl,./benchmarking/problems/triangle-tireworld/p03.pddl
...
...
...
```

**NOTE:** file `benchmarking/problems/instances.csv` contains _all_ problems available under `./benchmarking/problems`:

The script [benchmarking/src/generate_instances_csv.py](benchmarking/src/generate_instances_csv.py) is able to generate an instance file for a root folder of problems:

```shell
$ python benchmarking/src/generate_instances_csv.py benchmarking/problems instance.csv
```

This will generate file `benchmarking/problems/instance.csv` listing all problem instances found in folder `benchmarking/problems/`. Note this script is dependant on how the root problem folder is organized. In this case, each scenario has a folder, and then all problems are files in such folder. Different problem instance structures will require adaptation of such a script.

## 2. Experiment configuration file

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

## 3. API parsing functions

An important step is to program all the API functions necessary to _run_ a benchmarking experiment and produce a corresponding _report_. Those functions (and constants) will need to be specified in file [`benchmarking/src/domain_spec.py`](benchmarking/src/domain_spec.py). While the benchmarking scripts are domain-independent, these functions will depend on the specific domain being tested. In this case, it is FOND planning problems using the CFOND-ASP planner. **NOTE:** Only this file needs to be produced/adapted for benchmarking any setting!

The following two functions take the output folder of an instance run and parse output log files to extract useful information:

- `is_solved`: states whether problem instance been solved successfully.
- `get_report_row`: list of values to to be reported for extract stats as they will be reported in the csv report.

Note these functions will generally make use of other private functions to parse output files as needed.

The following two constants need to be defined:

- `REPORT_FILE`: name of the report CSV file (e.g., `report.csv`)
- `REPORT_HEADER`: list of header for the report CSV file

Finally, function `get_exec_cmd` should return the specific execution command for one instance run as a string.


## 4. Run benchmarking experiment

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

It will also save the output of each run using folder structure `scenario/id/solver/`. For example, folder `blocksworld/p04/asp1` will have all the files corresponding to the run of solver `asp1` against the problem `p04` within the scenario `blocksworld`.

Once finished, a CSV file `report.csv` is also left in the output folder.

One can also only re-generate the report by using the `--skip` option (all ran instances will be skiped) or even directly use the report script on the output folder:

```shell
$ python benchmarking/src/report.py output-bench
```

Note the report script will assume the structure produced by the benchmarking scripts in the output, namely,  `scenario/problem/solver`.

The report CSV file will look like this:

```csv
scenario,id,solver,SAT,time,memory,timeout,memoryout,policysize
doors,p01,asp4,True,-1,0,135.4375,0,5
doors,p01,asp1,True,-1,0,95.42578125,0,5
doors,p02,asp4,True,-1,0,179.89453125,0,7
doors,p02,asp1,True,-1,0,170.06640625,0,7
doors,p03,asp4,True,-1,0,141.73828125,0,9
doors,p03,asp1,True,-1,0,196.2890625,0,9
miner,p01,asp4,True,-1,0,306.65625,0,18
miner,p01,asp1,True,-1,0,260.47265625,0,18
miner,p02,asp4,True,-1,0,275.8359375,0,15
miner,p02,asp1,True,-1,0,258.15234375,0,15
miner,p03,asp4,True,-1,0,336.83203125,0,14
miner,p03,asp1,True,-1,0,309.6875,0,14
```

Note the first three columns are domain independent and will always be there, but the remaining ones will depend on the specific setting being benchmarked (in this case FOND problems).



