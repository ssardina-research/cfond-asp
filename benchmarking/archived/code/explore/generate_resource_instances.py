"""
This script generates instances to benchmark compactness and execution optimality tradeoff
"""
import os
from itertools import chain, combinations

OUTPUT_DIR = "./problems/examples/concepts/controller"
VARS = ['p', 'q', 'r', 's', 't', 'u']


def all_subsets(ss):
    return chain(*map(lambda x: combinations(ss, x), range(0, len(ss)+1)))


def generate_domain(num_propositions: int, possibilities: int=1):
    """
    (define (domain compact)
      (:requirements :typing :strips :non-deterministic)
      (:types step)
      (:predicates (process-at ?s - step)
           (p1-at ?s - step)
           (p2-at ?s - step)
           (next-step ?prev - step ?next - step)
           (p1)
           (p2)
      )
      (:action progress-p
        :parameters (?from - step ?to - step)
        :precondition (and (process-at ?from) (next-step ?from ?to) (p1) (p2))
        :effect (and (process-at ?to) (not (process-at ?from))
             (oneof
                (and (p1) (p2))
                (and (p1) (not (p2)))
                (and (not (p1)) (p2))
                (and (not (p2)) (not (p2)))
                )
            )
      )
      (:action fill-p1
        :parameters (?s - step)
        :precondition (and (p1-at ?s) (process-at ?s))
        :effect (and (not (p1-at ?s)) (p1)))

      (:action fill-p2
        :parameters (?s - step)
        :precondition (and (p2-at ?s) (process-at ?s))
        :effect (and (not (p2-at ?s)) (p2)) )
    )


    :param num_propositions:
    :param possibilities:
    :return:
    """
    domain_str = [f"(define (domain compact){os.linesep}", f"(:requirements :typing :strips :non-deterministic){os.linesep}", f"(:types step){os.linesep}",
                  f"(:predicates (process-at ?s - step){os.linesep}", f"(next-step ?prev - step ?next - step){os.linesep}"]
    for i in range(num_propositions):
        for j in range(possibilities):
            var = VARS[j]
            proposition = f"{var}{i+1}"
            domain_str.append(f"    ({proposition}-at ?s - step){os.linesep}")
            domain_str.append(f"    ({proposition}){os.linesep}")

    domain_str.append(f"){os.linesep}")

    for j in range(possibilities):
        var = VARS[j]
        propositions = []
        for i in range(num_propositions):

            proposition = f"{var}{i+1}"
            propositions.append(proposition)
            domain_str.append(f"(:action fill-{proposition}{os.linesep}")
            domain_str.append(f"    :parameters (?s - step){os.linesep}")
            domain_str.append(f"    :precondition( and ({proposition}-at ?s)(process-at ?s)){os.linesep}")
            domain_str.append(f"    :effect( and (not ({proposition}-at ?s))({proposition}))){os.linesep}")

        subsets = all_subsets(propositions)
        domain_str.append(f"(:action progress-{var}{os.linesep}")
        domain_str.append(f"    :parameters (?from - step ?to - step){os.linesep}")
        bracketed = [f"({p})" for p in propositions]
        domain_str.append(f"    :precondition( and (process-at ?from)(next-step ?from ?to) {''.join(bracketed)}){os.linesep}")
        domain_str.append(f"    :effect( and (process-at ?to)(not (process-at ?from)){os.linesep}")
        domain_str.append(f"        (oneof{os.linesep}")

        for subset in subsets:
            _lines = ["        (and"]
            for p in propositions:
                if p in subset:
                    _lines.append(f"({p})")
                else:
                    _lines.append(f"(not({p}))")
            _lines.append(f"){os.linesep}")
            domain_str.append(''.join(_lines))
        domain_str.append(f"))){os.linesep}")

    domain_str.append(f"){os.linesep}")

    with open(f"{OUTPUT_DIR}/domain{num_propositions}-{possibilities}.pddl", "w+") as f:
        f.writelines(domain_str)


def generate_problem(num_propositions, num_actions, possibilities):
    """
    (define (problem step-3)
      (:domain compact)
      (:objects l1 l2 l3 - step)
      (:init (process-at l1)
        (next-step l1 l2)
        (next-step l2 l3)


        (p1-in l1)
        (p1-in l2)
        (p1-in l3)

        (p2-in l1)
        (p2-in l2)
        (p2-in l3)

        (p1)
        (p1)
    )
      (:goal (process-at l3)))

    :param num_actions:
    :return:
    """
    steps = [f"l{i + 1}" for i in range(num_actions)]
    problem_str = [f"(define (problem step{num_actions}){os.linesep}", f"(:domain compact){os.linesep}", f"(:objects {' '.join(steps)} - step){os.linesep}",
                   f"(:init (process-at l1){os.linesep}"]
    for i in range(num_actions - 1):
        problem_str.append(f"(next-step {steps[i]} {steps[i + 1]}){os.linesep}")
    for j in range(possibilities):
        var = VARS[j]
        propositions = [f"{var}{i+1}" for i in range(num_propositions)]
        steps = [f"l{i+1}" for i in range(num_actions)]

        for p in propositions:
            problem_str.append(f" ({p}){os.linesep}")
            for s in steps:
                problem_str.append(f" ({p}-at {s}){os.linesep}")


    problem_str.append(f"){os.linesep}")
    problem_str.append(f"(:goal (process-at {steps[-1]}))){os.linesep}")

    with open(f"{OUTPUT_DIR}/p{num_propositions}-{num_actions}-{possibilities}.pddl", "w+") as f:
        f.writelines(problem_str)


def generate(num_propositions, num_actions, possibilities):
    generate_domain(num_propositions, possibilities)
    generate_problem(num_propositions, num_actions, possibilities)


if __name__ == "__main__":
    generate(2, 8, 5)
