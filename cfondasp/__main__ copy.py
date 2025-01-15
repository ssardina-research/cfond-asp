import argparse
import os

from pddl.formatter import domain_to_string, problem_to_string

from .normalizer import normalize
from .determizer import determinize
from .pddl import parse_domain_problem

from .helpers.base import is_url

import io
import requests

def main():
    parser = argparse.ArgumentParser(description="Utilities to process FOND PDDL")

    parser.add_argument("command", choices=["check", "determinize", "normalize"])
    parser.add_argument("--input", required=True, help="Input domain file/url")
    parser.add_argument("--output", help="Output domain file")
    parser.add_argument("--outproblem", help="Optional output problem file")
    parser.add_argument(
        "--suffix-domain",
        default="NEW",
        help="Suffix for the resulting domain (Default: %(default)s)",
    )
    parser.add_argument(
        "--prefix",
        default="DETDUP",
        help="Prefix for determinized action outcome name (Default: %(default)s)",
    )
    parser.add_argument(
        "--suffix", default="", help="Suffix for determinized action outcome name"
    )

    parser.add_argument(
        "--console", action="store_true", help="Print the domain after processing"
    )
    args = parser.parse_args()

    # handle input which could be a file or a url
    input_file = args.input
    if is_url(args.input):
        try:
            r = requests.get(args.input)
            if r.status_code != 200:
                print("Error: input url wrong or not found; status code received:", r.status_code)
                exit(1)
            input_file = io.StringIO(r.content.decode("utf-8"))
        except requests.ConnectionError as e:
            print("Error: input url wrong or not found:", e)
            exit(1)
    elif not os.path.isfile(args.input):
        print("Error: input url/file wrong or not found:", args.input)
        exit(1)

    # if fond_domain is None:
    #     parser.error("a domain is needed for this tool")

    # the input may be a domain alone or a domain+problem
    fond_domain, fond_problem = parse_domain_problem(input_file)

    if fond_domain is None:
        parser.error("a domain is needed for this tool")

    if (
        (args.command in ["determinize", "normalize"])
        and (not args.output)
        and (not args.console)
    ):
        parser.error(f"--output is required for {args.command} command")

    if args.command == "check":
        print("\n  Checking domain/problem file (if parsed well, domain/problem is printed nicely)...\n")
        if fond_domain:
            print(domain_to_string(fond_domain))
        if fond_problem is not None:
            print(problem_to_string(fond_problem))
        return

    elif args.command == "determinize":
        new_domain = determinize(
            fond_domain,
            dom_suffix=args.suffix_domain,
            op_prefix=args.prefix,
            op_suffix=args.suffix,
        )

    elif args.command == "normalize":
        new_domain = normalize(fond_domain, dom_suffix=args.suffix_domain)

    if args.output:
        with open(args.output, "w") as f:
            f.write(domain_to_string(new_domain))

            # write the problem (if any) in the same file as new domain
            if fond_problem is not None and args.outproblem is None:
                f.write("\n\n")
                f.write(problem_to_string(fond_problem))

    # update domain name in problem to match new domain name
    # NOTE: we need to access the private data of the object bc there is no setter :-(
    if fond_problem is not None:
        fond_problem._domain_name = (
            new_domain.name
        )

    # write the problem (if any) in a separate problem file
    if args.outproblem and fond_problem is not None:
        with open(args.outproblem, "w") as f:
            f.write(problem_to_string(fond_problem))

    if args.console:
        print(domain_to_string(new_domain))

        if fond_problem is not None:
            print(problem_to_string(fond_problem))


if __name__ == '__main__':
    main()
