# FOND Translators

This is a Python script that takes a non-deterministic PDDL (with `oneof` clauses) and yields a SAS _determinization_ encoding of the problem.

Example run:

```shell
$ python translate.py tests/acrobatics/domain.pddl tests/acrobatics/p1.pddl
```

By default, it generates a file `output.sas` with the SAS encoding of the determinization of the original non-deterministic problem. An alternative SAS filename can be given via `--sas-file` option.

This translator basically does two things:

1. First it translates all non-deterministic actions, into a collection of deterministic actions, each corresponding to one deterministic effect of the original non-deterministic action.
2. It then runs the original SAS translator from [FastDownard](https://github.com/aibasel/downward/tree/main/src/translate) system for classical deterministic planning problems.

This determinization SAS encoding has been used by various planners:

* FIP.
* [PRP](https://github.com/ssardina-planning/planner-for-relevant-policies).
* [FOND-SAT](https://github.com/ssardina-planning/FOND-SAT).

This repo basically has factored out such encoding into its own repo for modularity and further development as an independent tool.

Other FOND planners (like [myND](https://github.com/ssardina-planning/myND) and [Paladinus](https://github.com/ramonpereira/paladinus)) use a translation to SAS, but a different one that does not include determinization of the domain.

