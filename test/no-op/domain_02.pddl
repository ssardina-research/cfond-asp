; p1 (q): has strong-cyclic plan with one step (repeat sq) but no strong plan (can get stuck in a self-loop)
; p2 (q and r): no solution, never makes r true
;
; python -m cfondasp test/no-op/domain_02.pddl test/no-op/p2.pddl --translator-path ~/PROJECTS/planning/FOND/parsers/translator-fond.git/translate/translate/translate.py --dump-cntrl
(define (domain nooptest)
	(:requirements :strips :non-deterministic)
	(:predicates
		(p)
		(q)
		(r) ;; irrelevant proposition
	)

	;; make q true or no-op
	(:action sq
		:parameters ()
		:precondition (p)
		:effect (oneof (q) (and))
	)

)