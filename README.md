# CFOND-ASP: A Declarative Approach to Compact Controllers for FOND Planning via Answer Set Programming

CFOND-ASP is a FOND planner based on Answer Set Programming that computes compact controller solutions. It was inspired by a synthesis between [FOND-SAT](https://github.com/tomsons22/FOND-SAT) and [PRP](https://github.com/QuMuLab/planner-for-relevant-policies) planners.

The planner and its underlying technique were reported in the following paper:

* Nitin Yadav, Sebastian Sardiña: [A Declarative Approach to Compact Controllers for FOND Planning via Answer Set Programming](https://doi.org/10.3233/FAIA230593). ECAI 2023: 2818-2825

The `benchmarks/` folder contains problem instances, while folder `experiments/` contains the experimental framework; see [`README.md`](experiments/README.md) in that folder for more information.

## Requirements

The following software need to be available:

- Python 3.11+ with dependencies as per `requirements.txt`.
- [Clingo](https://potassco.org/clingo/) 5.5+ ASP solver.
  - Note version 5.4 does not support chained comparisons used of the form `X < Y < Z`.
- [SAS Translator](https://github.com/aibasel/downward/tree/main/src/translate) from [downward library](https://github.com/aibasel/downward).
  - This translates a deterministic PDDL domain and problem to an (optimized) SAS encoding. Note only the Python-based translator is used by CFOND-ASP.

#### FOND Translator to SAS

The planner uses a translator determinization system, which converts a FOND PDDL instance to a one-outcome determinized SAS version (i.e., every effect of an action becomes an action).

The FOND translator is under [src/translator-fond/](src/translator-fond/) and is a dump of commit [792f331](https://github.com/ssardina-research/translator-fond/tree/792f3317d3a8d7978a13cc41a48b7fd12f7690bc) in branch [fd22.12](https://github.com/ssardina-research/translator-fond/tree/fd22.12) in the [translator-fond](https://github.com/ssardina-research/translator-fond/) GH repo. Note this is version is a modification of [Fast-downard release 22.12](https://github.com/aibasel/downward/tree/release-22.12.0) (December 16, 2022) SAS translator for FOND determinization. This is different from the PRP's translator, which is based on the 2011 SAS FD translator (available, with fixes, in release [2011 PRP](https://github.com/ssardina-research/translator-fond/releases/tag/2011-prp) in [translator-fond repo](https://github.com/ssardina-research/translator-fond/)).

## Install

The planner is distributed as a package and can then be installed via pip directly.


One can also install it from the repo itself:

```shell
$ pip install https://github.com/ssardina-research/cfond-asp
```

Alternatively, one can clone first and install the planner:

```shell
$ git clone https://github.com/ssardina-research/cfond-asp
$ cd cfond-asp
$ pip install .
```

> [!TIP]
> If you plan to develop on CFOND-ASP it can be useful to install the cloned repo as [editable project](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) via `pip install -e .`

Once installed, the planner is available via its CLI interface:

```shell
$ cfond-asp -h
usage: cfond-asp [-h] [--max_states MAX_STATES] [--min_states MIN_STATES] [--inc_states INC_STATES]
                 [--mode {solve,verify,determinise}] [--solution_type {strong,strong-cyclic}] [--timeout TIMEOUT]
                 [--model {fondsat,regression}] [--clingo_args CLINGO_ARGS] [--extra_constraints EXTRA_CONSTRAINTS]
                 [--filter_undo] [--use_backbone] [--domain_kb {triangle-tireworld,miner,acrobatics,spikytireworld}]
                 [--dump_cntrl] [--output OUTPUT]
                 domain problem

CFOND-ASP: A FOND planner for compact controllers via ASP. - Version: 0.1.5

positional arguments:
  domain                Domain PDDL file
  problem               Problem PDDL file
```

## Usage

The planner is offered as a binary application:

```shell
$ cfond-asp [options] fond_domain fond_problem
```

Use `-h` to get all options available.

Note this is equivalent to cloning the planner repo and from tis root folder execute:

```shell
$ python -m cfondasp [options] fond_domain fond_problem
 ```

The planner main script parses the input and solves the planning instance as follows:

1. Computes the all-outcome determinization of the FOND domain using [fond-utils](https://github.com/AI-Planning/fond-utils) project.
2. Translates (and grounds) the now deterministic all-outcome domain and problem instance to [SAS](https://www.fast-downward.org/TranslatorOutputFormat) encoding using the translator from [Fast-Downward](https://www.fast-downward.org/) available in [translator-fond](https://github.com/ssardina-research/translator-fond) repo.
3. Translate the SAS file to a ASP file `instance.lp`.
4. Call Clingo ASP solver with `instance.lp` and the chosen ASP planning solver model.

Resulting output files will be left in the corresponding output directory (`./output` by default), including Clingo output for each iteration (wrt controller size), SAS encoding and output, ASP instance used, and stat file.

For example to solve the `p03.pddl` problem from the `Acrobatics` domain:

```shell
$ cfond-asp  benchmarks/acrobatics/domain.pddl benchmarks/acrobatics/p03.pddl

2025-01-16 15:26:43 surface FondASP[1848420] INFO Solving benchmarks/acrobatics/domain.pddl with problem benchmarks/acrobatics/p03.pddl using backbone=False.
2025-01-16 15:26:43 surface FondASP[1848420] INFO  -Solving with numStates=1.
2025-01-16 15:26:43 surface FondASP[1848420] INFO  -Solving with numStates=2.
2025-01-16 15:26:43 surface FondASP[1848420] INFO  -Solving with numStates=3.
2025-01-16 15:26:43 surface FondASP[1848420] INFO  -Solving with numStates=4.
2025-01-16 15:26:43 surface FondASP[1848420] INFO  -Solving with numStates=5.
2025-01-16 15:26:43 surface FondASP[1848420] INFO  -Solving with numStates=6.
2025-01-16 15:26:43 surface FondASP[1848420] INFO  -Solving with numStates=7.
2025-01-16 15:26:43 surface FondASP[1848420] INFO  -Solving with numStates=8.
2025-01-16 15:26:43 surface FondASP[1848420] INFO  -Solving with numStates=9.
2025-01-16 15:26:44 surface FondASP[1848420] INFO  -Solving with numStates=10.
2025-01-16 15:26:44 surface FondASP[1848420] INFO  -Solving with numStates=11.
2025-01-16 15:26:44 surface FondASP[1848420] INFO  -Solving with numStates=12.
2025-01-16 15:26:44 surface FondASP[1848420] INFO  -Solving with numStates=13.
2025-01-16 15:26:45 surface FondASP[1848420] INFO  -Solving with numStates=14.
2025-01-16 15:26:45 surface FondASP[1848420] INFO  -Solving with numStates=15.
2025-01-16 15:26:46 surface FondASP[1848420] INFO Solution found for instance (benchmarks/acrobatics/domain.pddl, acrobatics/p03.pddl)!
2025-01-16 15:26:46 surface FondASP[1848420] INFO Number of states in controller: 16
2025-01-16 15:26:46 surface cfondasp.__main__[1848420] WARNING Time taken: 2.9394077729957644
```

Use `--dump_cntrl` to dump controller found, if any, into text and JSON formats.

### Solver configurations available

The available ASP solver configurations, as reported in the ECAI23 paper, can be found under folder [src/asp/](src/asp/).

For strong-cyclic solutions (chosen via `--model`):

- `controller-fondsat`: encoding following FONDSAT in propagating negative propositions forward.
- `controller-reg`: encoding implementing weakest-precondition via regression (like PRP).

For strong solutions (via `--solution-type strong`), the encoding solver used is [`controller-strong.lp`](src/asp/controller-strong.lp).

### Clingo parameters

To pass specific argument to Clingo use `--clingo_args` as a quoted string. For example, to tell Clingo to use 4 threads and tell Clingo this is a single-shot task:

```shell
$ cfond-asp benchmarks/acrobatics/domain.pddl benchmarks/acrobatics/p03.pddl --clingo-args '-t 4 --single-shot'

...
2024-01-12 15:05:45 nitin FondASP[195707] INFO Solution found for id benchmarks/acrobatics/domain.pddl, benchmarks/acrobatics/p03.pddl!
2024-01-12 15:05:45 nitin __main__[195707] INFO Time(s) taken:1.3016068750002887
```

### Use backbone for minimum controller size estimation

To use _backbone_ size estimation (a lower bound on the size of the controller) to reduce the number of iterations, use `--use-backbone` option:

```shell
$ cfond-asp benchmarks/acrobatics/domain.pddl benchmarks/acrobatics/p03.pddl  --clingo-args '-t 4' --use-backbone True

...
2024-01-12 15:06:35 nitin FondASP[195939] INFO Solution found for id benchmarks/acrobatics/domain.pddl, benchmarks/acrobatics/p03.pddl!
2024-01-12 15:06:35 nitin __main__[195939] INFO Time(s) taken:1.2567479549907148
```

### Use domain knowledge

One can incorporate additional domain (control) knowledge in the planner by specifying additional ASP code, usually integrity constraints forbidding certain situations, and use option `--extra-constraints`.

For example, to tell the planner to completely _exclude_ action `jump` in the `Acrobatics` domain, we create a new file with the following ASP constraint:

```prolog
:- policy(State, Action), state(State), actionType("jump-over", Action).
```

If the file is called `acrobatics.lp`, one can then run the planner with option `--extra-constraints`:

```shell
$ cfond-asp benchmarks/acrobatics/domain.pddl benchmarks/acrobatics/p03.pddl  --clingo-args '-t 4' --use-backbone --extra-constraints ./acrobatics.lp

...
Solution found for id /home/nitin/Work/Software/cfond-asp/benchmarks/acrobatics/domain.pddl, /home/nitin/Work/Software/cfond-asp/benchmarks/acrobatics/p03.pddl!
2024-01-12 15:15:58 nitin __main__[198321] INFO Time(s) taken:0.9603760419995524
```

### Verification of controller

To _verify_ a strong-cyclic solution one can set the mode to `verify` via option `--mode`.

For example, to verify the solution for the `p03.pddl` problem from the `Acrobatics domain`:

```shell
$ cfond-asp benchmarks/beam-walk/domain.pddl benchmarks/beam-walk/p03.pddl --mode verify

2024-01-12 14:45:31 nitin FondASP[192070] INFO Solution is sound? True
2024-01-12 14:45:31 nitin __main__[192070] INFO Time(s) taken:0.032270914001856
```

This will first translate Clingo output to a readable controller format (see the file `controller.out` in the output directory), and then check the controller found is indeed strong-cyclic.

Verification result will be saved in file `verify.out`.

### Determinisation of instance

To only determinise the instance into the corresponding SAS encoding use the `determise` mode:

```shell
$ cfond-asp benchmarks/beam-walk/domain.pddl benchmarks/beam-walk/p03.pddl --mode determinise
```

This will just produce the corresponding domain determinization and its SAS encoding, but it will not solve it.

The determinisation and SAS encoder is done by the code under [`src/translator-fond/`](src/translator-fond/) which has been borrowed from the Fast-Downward codebase.

## Experiments

The set of experiments in ECAI23 paper were re-done using the [Benchexec](https://github.com/sosy-lab/benchexec) framework. Details can be found under [experiments/](experiments/README.md).

Two more configurations of the planner were added, using the FOND-SAT forward propagation of atoms (`ASP1-fsat` and `ASP2-fsat`) besides the regression-based configurations (`ASP1-reg` and `ASP2-reg`):

![sdasd](experiments/stats/ecai23-redo-benchexec-jul24/cfond_benchexec_stats_plot_PRP.jpg)

![sdasd](experiments/stats/ecai23-redo-benchexec-jul24/cfond_benchexec_stats_plot_FONDSAT.jpg)


## Contributors

- Nitin Yadav (nitin.yadav@unimelb.edu.au)
- Sebastian Sardina (ssardina@gmail.com - sebastian.sardina@rmit.edu.au)
