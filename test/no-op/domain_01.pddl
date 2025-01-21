; p1: easy should have both strong and strong-cyclic solutions - just do sq and get the goal
;
; python -m cfondasp test/no-op/domain_01.pddl test/no-op/p2.pddl --translator-path ~/PROJECTS/planning/FOND/parsers/translator-fond.git/translate/translate/translate.py --dump-cntrl
(define (domain nooptest)
	(:requirements :strips)
	(:predicates
		(p)
		(q)
	)

	;; deterministically make q true
	(:action sq
		:parameters ()
		:precondition (p)
		:effect (q) 
	)
)
