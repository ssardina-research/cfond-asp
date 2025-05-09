# Experiments

This folder contains all the tools to run a full experiment.

As of July 2024, experiments were re-done using the [Benchexec](https://github.com/sosy-lab/benchexec) experimental framework, which allows reliable benchmarking and resource measurement.

[Benchexec](https://github.com/sosy-lab/benchexec) is an benchmarking framework that is able to reliably measure and limit resource usage of the benchmarked tool even if the latter spawns sub-processes. It also includes a program called [runexec](https://github.com/sosy-lab/benchexec/blob/main/doc/runexec.md) that _"can be used to easily execute a single command while measuring its resource consumption, similarly to the tool time but with more reliable time measurements and with measurement of memory usage"_.


- [Experiments](#experiments)
  - [Installation and setup](#installation-and-setup)
    - [Install alternative Python versions](#install-alternative-python-versions)
  - [Configuring an experiment benchmark: Tools + Tasks](#configuring-an-experiment-benchmark-tools--tasks)
  - [Running a benchmark experiment](#running-a-benchmark-experiment)
    - [Setting environment variables](#setting-environment-variables)
    - [Running an experiment](#running-an-experiment)
    - [Output of benchexec](#output-of-benchexec)
  - [Runexec tool: testing a single benchexec runs](#runexec-tool-testing-a-single-benchexec-runs)
  - [Analysis of experiments](#analysis-of-experiments)
    - [Extract Benchexec CSV stats tables](#extract-benchexec-csv-stats-tables)
    - [Generate coverage plots](#generate-coverage-plots)

## Installation and setup

Details on its installation and its working can be found [here](https://github.com/sosy-lab/benchexec/blob/main/doc/INSTALL.md). Please note that Benchexec works better with Linux kernel 6.1+.

The recommneded instructions for Ubuntu-based system is to install Benchexec from its [PPA](https://launchpad.net/~sosy-lab/+archive/ubuntu/benchmarking) system-wide:

```shell
$ sudo add-apt-repository ppa:sosy-lab/benchmarking
$ sudo apt update
$ sudo apt install Benchexec
...
The following additional packages will be installed:                       
  python3-coloredlogs python3-humanfriendly python3-pystemd            
Recommended packages:                                                                     
  cpu-energy-meter fuse-overlayfs                                                         
The following NEW packages will be installed:                  
  benchexec python3-coloredlogs python3-humanfriendly python3-pystemd 
```

As you can see, this will automatically install three more packages, including `python3-pystemd` that will set-up cgroups automatically. By doing this the benchexec package should be available system-wide and from all Python virtual environments used (check [this explanation](https://medium.com/@sachinsoni600517/how-python-search-for-imported-module-package-76cf0da5f690)).

After that, _create a virtual environment_ sandbox for the project, for example using `venv` we create it inside the main project folder `/mnt/projects/fondasp`:

```shell
# create virtual environment in project folder
$ python -m venv /mnt/projects/fondasp/cfond-p10

# activate virtual environment
$ source /mnt/projects/fondasp/cfond-p10/bin/activate
```

Next, we install CFOND-ASP planner in the just created environment as a package:

```shell
$ pip install git+https://github.com/ssardina-research/cfond-asp
```

This will make the CFOND-ASP binary (`cfond-asp`) available.

> [!TIP]
> If you need a new install of Python (beyond just a virtual environment), consider using [pyenv](https://github.com/pyenv/pyenv) which will allow you to localy install any Python version and corresponding virtual environments.

### Install alternative Python versions

You can setup a new Python version for it via [pyenv](https://github.com/pyenv/pyenv):

```shell
# setup new Python version and install all dependencies
$ pyenv install 3.12.7  # will install fresh Python under ~/.pyenv
$ pyenv shell 3.12.7  # activate python version (all)
```

## Configuring an experiment benchmark: Tools + Tasks

The above has set-up Benchexec and the planner CFOND-ASP. We assume we  the virtual environment created is active, that we have already cloned the CFOND-ASP repo somewhere (in our NecTAR setup, it is in `/mnt/projects/fondasp/cfond-asp.git`). The experimental framework for Benchexec is located in folder `experiments/benchexec`.

To benchmark a particular solver (possibly under different settings/configurations), we provide:

1. A **solver tool** Python script, defining the solver that will be benchmarked. This includes the executable of the solver and the processing of its output (e.g., to extract policy size).
   * Tool definitions for the solvers used can be found under [benchexec/tools](benchexec/tools).
2. A set of **tasks** defining each instance to be solved, as an YAML file specifying input files (domain and problem) and output folder.
   * Tasks for the plannig problems instances in the planner `benchmark/` folder can be found under [benchexec/tasks](benchexec/tasks/).
   * These tasks have been generated automatically using script [benchexe/gen_tasks.py](benchexec/gen_tasks.py). From `experiments/` folder:

      ```shell
      $ python benchexec/gen_tasks.py ../benchmarks benchexec/ --prefix ../../benchmarks
      ```

      This will add all the `.yml` task files into folder `benchexec/tasks`, using benchmark folder `../benchmarks` and input files will be prefixed with path `../../

3. A main **benchmark definition**, as an XML file, defining solver tool, resource limits, tasks to run, and run definitions. One creates one XML file per tool.
   * Benchmark definition XML files can be found under [`benchexec/`](benchexec/).
   * Note that most XML files define various runs definition, for the same solver under different configurations.

More explanation on this can be found [here](https://github.com/sosy-lab/benchexec/blob/main/doc/benchexec.md) and definition of other terms can be found in the [Glossary](https://github.com/sosy-lab/benchexec/blob/main/doc/INDEX.md).

> [!NOTE]
> The experiments provided uses the benchmark set shiped with the CFOND-ASP planner. A more "official" and comprehensive set of FOND planning problems can be found in repo [AI-Planning/fond-domains/](https://github.com/AI-Planning/fond-domains/).

## Running a benchmark experiment

Here we will demonstrate how we ran our experiments using the Australian [NECTAR cluster infrastructure](https://ardc.edu.au/services/ardc-nectar-research-cloud/). The CPUs are as follows:

```
processor	: 31
vendor_id	: AuthenticAMD
cpu family	: 23
model		: 49
model name	: AMD EPYC-Rome Processor
stepping	: 0
```

> [!WARNING]
> While the machines have many cores, we found that running more than 8 experiments at the same time yields high-variance, non-replicable, performance. So we only run 8 tasks in parallel. See [this isue](https://github.com/ssardina-research/app/discussions/97).

In the explanations below, the CFOND-ASP repo was cloned in `/mnt/projects/fondasp/cfond-asp.git`, which is a network filesystem. However, we save the output data in the _local_ filesystem `/mnt/data/fondasp/benchexec-exp`, which is faster than the project folder.

### Setting environment variables

We first need to make sure the **various _tool_ Python modules/classes** (as used in the XML benchmark definitions) **are available**. This can be done by changing variable [PYTHONPATH](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH) so that module `benchexec` can be found by Python (note that we are in a folder different from the CFOND-ASP local copy, so need to give the full path):

```shell
$ export PYTHONPATH=/mnt/projects/fondasp/cfond-asp.git/experiments/benchexec/
```

Second, we need to make sure that **Benchexec has access to all binaries** used by the various tools (e.g., planning systems). One way is to make all those tools available in the `PATH`, but this can be cumbersome. A cleaner way is to setup a `bin/` folder containing symbolic links to all the solver binaries used and then use option `--tool-directory` (see below), which tells Benchexec where the tools' _executables_ (e.g., the `prp` binary) are located. 

> [!NOTE]
> If this parameter is not given, Benchexec searches in the directories of the `PATH` environment variable and in the current directory. So an alternative is to add the `bin/` folder created in the `PATH` via `export PATH=$PATH:$PWD/bin`


For CFOND-ASP, its corresponding tool `cfondasp.py` assumes the planner has been installed as a package and hence the binary `cfond-asp` available in the Python virtual environment. The name of the binary for the other solvers can be found in function `executable` of each tool definition. We have already installed the planner above in the current virtual environment.

Finally, make sure the **[SAS translator for FOND](https://github.com/ssardina-research/translator-fond/tree/main/translate) is available in the `PATH`**, either by setting a symbolic link to `translate.py` under the above `bin/` folder or adding it to the path:

```shell
$ export PATH=$PATH:/mnt/projects/fondasp/translator-fond.git/translate/translate
```

To double check, test a run of CFOND-ASP:

```shell
$ cfond-asp /mnt/projects/fondasp/cfond-asp-private.git/benchmarks/acrobatics/domain.pddl /mnt/projects/fondasp/cfond-asp-private.git/benchmarks/acrobatics/p01.pddl 
```

The successful run will leave the output files under `output/`.

At this point the Benchexec framework has access to the Python tool modules, the tool executable themselves, and the SAS translator for FOND.

### Running an experiment

To benchmark a solver one passes the main benchmark definition XML file with the required arguments. We shall use below `benchmark-fondasp.xml` to benchmark CFOND-ASP. 

The following command benchmarks the solver against the `MINER-SMALL` tasks set (defined in the XML file and containing the first nine problem instances in the miner domain), running 8 instances in in parallel (`-N 8`) with two cores per problem (`-c 2`):

```shell
$ benchexec /mnt/projects/fondasp/cfond-asp-private.git/experiments/benchexec/benchmark-fondasp.xml -t MINER-SMALL -N 8 -c 2 --read-only-dir / --overlay-dir /mnt/data/fondasp
2025-02-03 21:51:52 - WARNING - No propertyfile specified. Score computation will ignore the results.                                                                                        
2025-02-03 21:51:52 - INFO - Unable to find pqos_wrapper, please install it for cache allocation and monitoring if your CPU supports Intel RDT (cf. https://gitlab.com/sosy-lab/software/pqos
-wrapper).                                                                                                                                                                                   
                                                                                                                                                                                             
executing run set 'cfondasp-fsat.MINER-SMALL'     (9 files)                                                                                                                                  
21:51:52   starting   miner_01.yml                                                                                                                                                           
21:51:52   starting   miner_02.yml                                                                                                                                                           
21:51:52   starting   miner_03.yml                                                                                                                                                           
21:51:52   starting   miner_04.yml                                                                                                                                                           
21:51:52   starting   miner_05.yml                                                                                                                                                           
21:51:52   starting   miner_06.yml                                                                                                                                                           
21:51:52   starting   miner_07.yml                                                                                                                                                           
21:51:52   starting   miner_08.yml                                                                                                                                                           
21:51:59              miner_02.yml            true                         7.31    6.41                                                                                                      
21:51:59   starting   miner_09.yml                                                                                                                                                           
21:52:00              miner_01.yml            true                         8.26    7.10                                                                                                      
21:52:00              miner_03.yml            true                         7.94    7.12                                                                                                      
21:52:17              miner_04.yml            true                        27.72   24.43                                                                                                      
21:52:17              miner_05.yml            true                        29.59   24.64                                                                                                      
21:52:22              miner_06.yml            true                        33.96   29.21                                                                                                      
21:52:29              miner_08.yml            true                        42.66   36.55                                                                                                      
21:52:44              miner_07.yml            true                        63.27   51.69                                                                                                      
21:52:50              miner_09.yml            true                        59.50   50.87                                                                                                      
                                                                                                                                                                                             
executing run set 'cfondasp-reg.MINER-SMALL'     (9 files)                                                                                                                                   
21:52:50   starting   miner_01.yml                                                                                                                                                           
21:52:50   starting   miner_02.yml                                                                                                                                                           
21:52:50   starting   miner_03.yml                                                                                                                                                           
21:52:50   starting   miner_04.yml                                                                                                                                                           
21:52:50   starting   miner_05.yml                                                                                                                                                           
21:52:50   starting   miner_06.yml                                                                                                                                                           
21:52:50   starting   miner_07.yml                                                                                                                                                           
21:52:50   starting   miner_08.yml                                                                                                                                                           
21:52:55              miner_02.yml            true                         5.88    4.56                                                                                                      
21:52:55   starting   miner_09.yml                                                                                                                                                           
21:52:56              miner_03.yml            true                         6.87    5.42                                                                                                      
21:52:56              miner_01.yml            true                         7.34    5.43                                                                                                      
21:53:10              miner_04.yml            true                        26.61   19.64                                                                                                      
21:53:12              miner_05.yml            true                        31.48   21.33                                                                                                      
21:53:18              miner_06.yml            true                        41.04   28.14                                                                                                      
21:53:26              miner_08.yml            true                        52.32   36.25                                                                                                      
21:53:42              miner_07.yml            true                        79.34   51.77                                                                                                      
21:53:42              miner_09.yml            true                        69.72   47.35                                                                                                      
                                                                                                                                                                                             
Statistics:             18 Files                                                                                                                                                             
  correct:               0                                                                                                                                                                   
    correct true:        0                                                                                                                                                                   
    correct false:       0                                                                                                                                                                   
  incorrect:             0                                                                                                                                                                   
    incorrect true:      0                                                                                                                                                                   
    incorrect false:     0                                                                                                                                                                   
  unknown:               0                                                                                                                                                                   
                                                                                                                                                                                             
In order to get HTML and CSV tables, run                                                                                                                                                     
table-generator results/benchmark-fondasp.2025-02-03_21-51-52.results.cfondasp-fsat.MINER-SMALL.xml.bz2 results/benchmark-fondasp.2025-02-03_21-51-52.results.cfondasp-reg.MINER-SMALL.xml.bz
2
```

The above shows that two run-sets (CFOND-ASP under two configurations) were run on 9 instances for Miner, which they are all accessible. The `true` labels signal that the problem was solved succesfully. The last two column
report CPU time and walltime (note CPU time is larger as each instance is using two cores; both metrics would be the same if `-c 1` is used).

>[!NOTE]
> We have not used `--tool-directory` because the executable `cfond-asp` is in the `PATH` already.
> If instead, we would run `benchmark-prp.xml` benchmark, we would use `--tool-directory ./bin` assumming `prp` executable has beebn linked in that folder. If this parameter is not given, Benchexec searches in the directories of the `PATH` environment variable and in the current directory.

> [!WARNING] 
> If you get error `Unsupported tool "tools.prp" specified. ImportError: No module named 'tools'`
> it is because the XML definition couldn't find the tool Python module. Remember to set the environment variable `PYTHONPATH` to make sure `benchexec/tools` is found by Python.

The following options refer to [container configurations](https://github.com/sosy-lab/benchexec/blob/main/doc/container.md#container-configuration):

* `--read-only-dir /`: allows the container to access all the file-system in _read_ mode.
* `--overlay-dir /mnt/data/fondasp`: allows Benchexec to access all `/mnt/data/fondasp` as an overlay transparent file system:
  * All the existing data there is accessible for read (unless explicitly hidden via `--hidden-dir`).
  * _New_ data/files can be written (e.g., log files of the run), but it will be done on RAMDISK and hence will be counted towards memory usage, unless `--no-tmpfs` option is used, in which case writes will go to disk and NOT counted as memory usage (note that even in this case, Linux may still write to cache memory if available! see thread discussion we had in issue [#1025](https://github.com/sosy-lab/benchexec/issues/1025)).
  * If we want to retrieve anything that is written by the execution, it has to be specified in the `<resultsfiles>` section in the XML configuration files. The retrieved files will be accessible under the Benchexec result folder (but by just a bulk copy a the end of the execution, not by writing directly there while running!).
* `--hidden-dir`: the host directory specified will be hidden in the container. This allows the process to use that directory "fresh" without clashing with whatever is already there in the host. In our case, we hide the directory where the output of the solver is meant to be located, in case such folder already exists in the host. If it does and we don't hide it, the solver will try to re-create the folder but since it does exist in the overlay in read-mode, the solver will crash with I/O error because it cannot remove a folder that is in already in the host.

> [!IMPORTANT] 
> By default, the container runs in isolation, with **writes to filesystem done in RAM memory**. If we want to give the container full direct access to some part of the file-system, we can use for example `--full-access-dir /home/$USER`. Then, anything that is done under `/home/$USER` will be as if running in the host directly. Not recommended!

Note that the `--overlay-dir` does give access to the host file system in the container, but only on read-mode for what already exists.

> [!WARNING]
> **[THIS MAY BE OLD INFO IN JAN 2025]**
> While in principle one should be able to use any overlay directory, it seems Benchexec creates a virtual home folder under `home/benchexec`, so it is hard-coded. See [this code](https://github.com/sosy-lab/benchexec/blob/64d73c47e05a1487727c4777e23863ce4ed4851a/benchexec/container.py#L55). So, if we give say `/home/ssardina`, Benchexec complains it cannot create such `home/benchexec`.

### Output of benchexec

Benchexec reports stats, logs, and corresponding out files for every executed run; check [here](https://github.com/sosy-lab/benchexec/blob/main/doc/run-results.md). 

All output files and folders will be placed under folder `results/` in the current directory unless explicitly specified otherwise via option `-o DIRECTORY`. All files will have the XML experiment filename as prefixes; and run values are stored in compressed files `.xml.bz2`

Refer below to understand how to extract state tables into CSV and HTML files and then process them via notebooks.

## Runexec tool: testing a single benchexec runs

We can use the [`runexec`](https://github.com/sosy-lab/benchexec/blob/main/doc/runexec.md) tool to run/test a particular script/program on the spot once (i.e., without XML, tools, etc. configurations).

Issue [#1025](https://github.com/sosy-lab/benchexec/issues/1025) discusses _When exactly is data written to disk by a process contained in the memory measurement?_

For example, the following runs PRP planner on container mode (default) and also recovers all the output files (note we run it from `$HOME/tmp` with 12MB memory limit):

```shell
$ cd $HOME/tmp
$ runexec --read-only-dir / --overlay-dir /home/ --result-files "*" --memlimit 12331392 /mnt/projects/fondasp/planners/prp/src/prp /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/domain.pddl /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/p5.pddl 
2025-02-09 18:14:13 - INFO - Starting command /mnt/projects/fondasp/planners/prp/src/prp /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/domain.pddl /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/p5.pddl
2025-02-09 18:14:13 - INFO - Writing output to output.log and result files to output.files
starttime=2025-02-09T18:14:13.784618+11:00
returnvalue=0
walltime=8.464726964011788s
cputime=8.448107s
memory=11874304B
blkio-read=0B
blkio-write=0B
pressure-cpu-some=0.000959s
pressure-io-some=0.000844s
pressure-memory-some=0s
```

The standard output will be saved into `output.log` and all files will be retrived into `output.files/` folder. As we can see, all resources used are reported, stating that the run took 8+ seconds and used 11874304 bytes, that is, 11MB.

If we specify a limit of 9MB, then it will fail and report memory termination (signal 9):

```shell
$ runexec --read-only-dir / --overlay-dir /home/ --result-files "*" --memlimit 9000000  /mnt/projects/fondasp/planners/prp/src/prp /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/domain.pddl /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/p5.pddl 
2024-07-20 19:08:18 - INFO - Starting command /mnt/projects/fondasp/planners/prp/src/prp /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/domain.pddl /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/p5.pddl
2024-07-20 19:08:18 - INFO - Writing output to output.log and result files to output.files
starttime=2024-07-20T19:08:18.170010+10:00
terminationreason=memory
exitsignal=9
walltime=0.11081427399949462s
cputime=0.112003s
memory=19996672B
blkio-read=0B
blkio-write=0B
pressure-cpu-some=0.000032s
pressure-io-some=0s
pressure-memory-some=0.000186s
```

Sometimes, it reports signal 9 (out of memory) as follows:

```shell
$ runexec --read-only-dir / --overlay-dir /home/ --result-files "*" --memlimit 8331392 /mnt/projects/fondasp/planners/prp/src/prp /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/domain.pddl /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/p5.pddl
2025-02-09 18:17:17 - INFO - Starting command /mnt/projects/fondasp/planners/prp/src/prp /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/domain.pddl /mnt/projects/fondasp/fond-domains.git/benchmarks/beam-walk/p5.pddl
2025-02-09 18:17:17 - INFO - Writing output to output.log and result files to output.files
2025-02-09 18:17:17 - CRITICAL - Error while starting '/mnt/projects/fondasp/planners/prp/src/prp' in '.': [Errno 0] Child process of RunExecutor terminated with exit signal 9.
terminationreason=failed
```

> [!NOTE]
> If we use the `--no-tmpfs` option, we are telling benchexec to NOT use RAMDISK and use the actual hard drive; file writting does not count towards memory usage.


## Analysis of experiments

### Extract Benchexec CSV stats tables

Benchexec will leave all outputs under folder `results/` (unless specified otherwise via `-o` option) and with prefix `<XML experiment file>.<DATE>`:

- `*.files` folder contains the run output files that were extracted as per `resultfiles` in the XML file.
- `*.logfiles.zip` contains the console output of each run
- `*.<rundefinition>.<task>.xml.bz2` contains the statistics for each run on task executed.
- `*.results.txt` contains the textual summary of the whole experiment ran.

For example:

```shell
$ ls -la results
total 56
drwxrwxr-x 3 ssardina ssardina  4096 Feb  9 20:01 .
drwxrwxr-x 4 ssardina ssardina  4096 Feb  9 19:59 ..
drwxrwxr-x 4 ssardina ssardina  4096 Feb  9 20:01 benchmark-fondasp.2025-02-09_19-59-41.files
-rw-rw-r-- 1 ssardina ssardina 17627 Feb  9 20:01 benchmark-fondasp.2025-02-09_19-59-41.logfiles.zip
-rw-rw-r-- 1 ssardina ssardina  5549 Feb  9 20:01 benchmark-fondasp.2025-02-09_19-59-41.results.cfondasp-fsat.MINER-SMALL.xml.bz2
-rw-rw-r-- 1 ssardina ssardina  5511 Feb  9 20:01 benchmark-fondasp.2025-02-09_19-59-41.results.cfondasp-reg.MINER-SMALL.xml.bz2
-rw-rw-r-- 1 ssardina ssardina  4540 Feb  9 20:01 benchmark-fondasp.2025-02-09_19-59-41.results.txt
```

You can generate a CSV/HTML table from the results in files `*.xml.bz2` for further analysis, for example via Pandas. Check how to generate these tables [HERE](https://github.com/sosy-lab/benchexec/blob/main/doc/table-generator.md).

When benchexec finishes it will print a message stating what command needs to be run to generate the standard CSV stat tables:

```shell
In order to get HTML and CSV tables, run
table-generator results/benchmark-fondasp.2025-02-09_19-59-41.results.cfondasp-fsat.MINER-SMALL.xml.bz2 results/benchmark-fondasp.2025-02-09_19-59-41.results.cfondasp-reg.MINER-SMALL.xml.bz2
```

In our example:

```shell
$ table-generator results/benchmark-fondasp.2025-02-09_19-59-41.results.cfondasp-fsat.MINER-SMALL.xml.bz2 results/benchmark-fondasp.2025-02-09_19-59-41.results.cfondasp-reg.MINER-SMALL.xml.bz2 
INFO:     results/benchmark-fondasp.2025-02-09_19-59-41.results.cfondasp-fsat.MINER-SMALL.xml.bz2
INFO:     results/benchmark-fondasp.2025-02-09_19-59-41.results.cfondasp-reg.MINER-SMALL.xml.bz2
INFO: Merging results...
INFO: The resulting table will have 9 rows and 12 columns (in 2 run sets).
INFO: ---> NO DIFFERENCE FOUND IN SELECTED COLUMNS
INFO: Generating table...
INFO: Writing HTML into results/results.2025-02-09_20-04-14.table.html ...
INFO: Writing CSV  into results/results.2025-02-09_20-04-14.table.csv ...
INFO: done

$ l results/*.csv
-rw-rw-r-- 1 ssardina ssardina 2.0K Feb  9 20:04 results/results.2025-02-09_20-04-14.table.csv
```

> [!WARNING]
> The generate CSV tables, the generator will require access to the tools used, so make sure you have set `PYTHONPATH` to point to where the `tools` Python module is located; [see above](#setting-environment-variables).


Note that the resulting CSV table will contain stats for two run definitions, `cfondasp-fsat` and `cfondasp-reg`. In those tables, each row is a _task_ and columns record the results on each _run definition_ (in our example, two). This means that for each run definition, there will be a set of columns with the same header. If you want to later analyse it or plot charts, you may need to pivot all these set of columns using a distinguish column to identify runs. The example says that there are 9 rows (9 tasks corresponding to the 9 planning instances), and 12 columns over 2 run sets, that is, each run definition will have 6 columns: `status`, `cputime (s)`, `walltime (s)`, ` memory (MB)`, `planner_time`, and `policy_size`. Observe the first four are experiment independent and will always be provided by Benchexec; the last two are experiment dependent and correspond to the `columns` section in the exeperiment XML file:

```xml
 <columns>
    <!-- <column> tags may be used to define columns in the result tables with data from the tool
    output. -->
    <column title="policy_size">policy_size</column>
    <column title="planner_time">planner_time</column>
  </columns>
```

If more than on run definition has been processed (more than one `xml.bz2`), the table generator may also generate a _difference_ table `*.diff.csv` that includes all the rows where the `status` column differ across run definitions. In our example, there were no differences (both solver configurations had the same status), as reported with `INFO: ---> NO DIFFERENCE FOUND IN SELECTED COLUMNS` in the console. However, you can check difference table [stats/ecai23-redo-benchexec-jul24/cfondasp-23-08-24/results.2024-09-02_07-34-19.diff.csv](stats/ecai23-redo-benchexec-jul24/cfondasp-23-08-24/results.2024-09-02_07-34-19.diff.csv) where it reports a total of 590 rows in the run set, of which 559 have different results wrt the four run definitions executed.

Finally, besides the CSV/HTML stat tables, if the XML definition states that some files/folders need to be recovered from the overlay (via the tag `<resultfiles>`), they will be also dumped into the  `results/` folder, with recovered data stored where the `output:` option field in the task YAML definitions specifies.

The output of our running example can be found in folder [stats/cfondasp-miner-small/](stats/cfondasp-miner-small/)

To learn about the outputs left by Benchexec, please check [HERE](https://github.com/sosy-lab/benchexec/blob/main/doc/benchexec.md#benchexec-results).

### Generate coverage plots

This is a two-step process.

First, **we process the Benchexec tables** via notebook [process_benchexec.ipynb](process_benchexec.ipynb) to extract two CSV files:

1. A flat table of stats, that can be used for further analysis and plotting, with the solver being recorded in a new column. Benchexec tables are not flatten and each run set contains its own columns.
2. A coverage table per domain and solver, typically reported in papers.

Second, we use **plot integrated time-coverage plots** using the Python notebook or R script available in [coverage-plots](https://github.com/ssardina-research/coverage-plots) repo.

![plot](stats/ecai23-redo-benchexec-jul24/cfond_benchexec_stats_plot_PRP.jpg)

![plot](stats/ecai23-redo-benchexec-jul24/cfond_benchexec_stats_plot_FONDSAT.jpg)

The solvers reported are:

- `ASP1-fsat`: CFOND-ASP with 1 thread using FOND-SAT forward propagation of negative atoms.
- `ASP1-reg`: CFOND-ASP with 1 thread using PRP regression-based propagation of atoms (i.e., weakest-precondition)
- `ASP2-fsat`: CFOND-ASP with 2 threads using FOND-SAT forward propagation of negative atoms with domain knowledge.
- `ASP2-reg`: CFOND-ASP with 1 thread using PRP regression-based propagation of atoms (i.e., weakest-precondition) with domain knowledge.
- `FSAT-GL`: FOND-SAT with Glucose SAT solver.
- `FSAT-MS`: FOND-SAT with Minizinc SAT solver.
- `PRP`: PRP FOND planner.
- `PAL`: [PALADINUS](https://github.com/ramonpereira/paladinus) FOND planner.

The benchmark used are the same as in the ECAI23 paper, which includes that used by [PRP](https://github.com/ssardina-research/planner-for-relevant-policies/) and the four domains introduced by [FOND-SAT](https://github.com/tomsons22/FOND-SAT):

> The set of FOND benchmarks includes the new domains introduced in [13], namely DOORS, ISLANDS, MINER, TIREWORLD-SPIKY, and TIREWORLD-TRUCK . The other classical FOND domains tested include ACROBATICS , BEAM-WALK , BLOCKSWORLD, CHAIN-OF-ROOMS, EARTH-OBSERVATION, ELEVATORS, FAULTS, FIRST-RESPONDERS, TIREWORLD, TRIANGLE-TIREWORLD, and ZENOTRAVEL. We only considered planning instances that are solvable. The total number of solvable instances are 210 for the new FOND domains and 348 for the classical FOND domains.


To run the R script in Linux: 

```shell
$ R < plots.R --no-save
```

The result is saved in file [stats/ecai23-redo-benchexec-jul24/cfond_benchexec_stats_R.png](stats/ecai23-redo-benchexec-jul24/cfond_benchexec_stats_R.png):

![plot](stats/ecai23-redo-benchexec-jul24/cfond_benchexec_stats_R.png)




