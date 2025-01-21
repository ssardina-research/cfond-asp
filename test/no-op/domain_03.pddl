; p1 (q): has strong-cyclic plan with one step (repeat sq) but no strong plan (can get stuck in a self-loop)
; p2 (q and r): has strong-cyclic plan with 2 steps (repeat sq ; repeat sq) but no strong plan (can get stuck in a self-loop) 
;
; python -m cfondasp test/no-op/domain_03.pddl test/no-op/p2.pddl --translator-path ~/PROJECTS/planning/FOND/parsers/translator-fond.git/translate/translate/translate.py --dump-cntrl
(define (domain nooptest)
	(:requirements :strips :non-deterministic)
	(:predicates
		(p)
		(q)
		(r)
	)

	;; Action to move while being on the beam
	(:action sq
		:parameters ()
		:precondition (p)
		:effect (oneof (q) (r))
	)
)
