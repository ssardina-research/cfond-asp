# A Declarative Approach to Compact Controllers for FOND Planning via Answer Set Programming

A FOND planner based on Answer Set Programming, inspired by a synthesis between [FOND-SAT](https://github.com/tomsons22/FOND-SAT) and [PRP](https://github.com/QuMuLab/planner-for-relevant-policies) planners.

The planner and its underlying technique were reported in the following paper:

* Nitin Yadav, Sebastian Sardiña: [A Declarative Approach to Compact Controllers for FOND Planning via Answer Set Programming](https://doi.org/10.3233/FAIA230593). ECAI 2023: 2818-2825

The `benchmarks/` folder contains problem instances, while folder `experiments/` contains the experimental framework; see [`README.md`](experiments/README.md) in that folder for more information.

## Requirements

- Python 3.11 with dependencies as per `requirements.txt`.
  - The listed Python packages may have other dependencies (e.g., `libxml2` and `libxslt` development packages).
- [Clingo](https://potassco.org/clingo/) 5.5+ ASP solver.
  - Note version 5.4 does not support chained comparisons used of the form `X < Y < Z`.

#### FOND Translator to SAS

The planner uses a translator determinization system, which converts a FOND PDDL instance to a one-outcome determinized SAS version (i.e., every effect of an action becomes an action).

The FOND translator is under [src/translator-fond/](src/translator-fond/) and is a dump of commit [792f331](https://github.com/ssardina-research/translator-fond/tree/792f3317d3a8d7978a13cc41a48b7fd12f7690bc) in branch [fd22.12](https://github.com/ssardina-research/translator-fond/tree/fd22.12) in the [translator-fond](https://github.com/ssardina-research/translator-fond/) GH repo. Note this is version is a modification of [Fast-downard release 22.12](https://github.com/aibasel/downward/tree/release-22.12.0) (December 16, 2022) SAS translator for FOND determinization. This is different from the PRP's translator, which is based on the 2011 SAS FD translator (available, with fixes, in release [2011 PRP](https://github.com/ssardina-research/translator-fond/releases/tag/2011-prp) in [translator-fond repo](https://github.com/ssardina-research/translator-fond/)).


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

Use `--dump_cntrl` to dump controller found, if any, into text and JSON formats.

## Solver configurations available

The available ASP solver configurations, as reported in the ECAI23 paper, can be found under folder [src/asp/](src/asp/).

For strong-cyclic solutions (chosen via `--model`):

- `controller-fondsat`: encoding following FONDSAT in propagating negative propositions forward.
- `controller-reg`: encoding implementing weakest-precondition via regression (like PRP).

For strong solutions (via `--solution_type strong`), the encoding solver used is [`controller-strong.lp`](src/asp/controller-strong.lp).

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

This will first translate Clingo output to a readable controller format (see the file `controller.out` in the output directory), and then check the controller found is indeed strong-cyclic.

Verification result will be saved in file `verify.out`.

### Determinisation of instance

To only determinise the instance into the corresponding SAS encoding use the `determise` mode:

```shell
$ python src/python/main.py benchmarking/problems/beam-walk/domain.pddl benchmarking/problems/beam-walk/p03.pddl --mode determinise
```

This will just produce the corresponding SAS one-outcome determinised encoding of the problem instance, but it will not solve it.

The determinisation and SAS encoder is done by the code under [`src/translator-fond/`](src/translator-fond/) which has been borrowed from PRP codebase.


## Contributors

- Nitin Yadav (nitin.yadav@unimelb.edu.au)
- Sebastian Sardina (ssardina@gmail.com - sebastian.sardina@rmit.edu.au)
