; p1: easy should have both strong and strong-cyclic solutions - just do sq and get the goal
;
; python -m cfondasp test/no-op/domain_01.pddl test/no-op/p2.pddl --translator-path ~/PROJECTS/planning/FOND/parsers/translator-fond.git/translate/translate/translate.py --dump-cntrl
(define (domain nooptest)
	(:requirements :strips)
	(:predicates
		(p)
		(q)
		(r)	;; totally irrelevant predicate
	)

	;; deterministically make q true
	(:action setq
		:parameters ()
		:precondition (p)
		:effect (q)
	)

	;; just touch irrelevant predicate r
	; (:action setnr
	; 	:parameters ()
	; 	:precondition ()
	; 	:effect (not (r))
	; )

		; (:action bad1	;; makes precondition of landmark action setq false forever
	; 	:parameters ()
	; 	:precondition ()
	; 	:effect (not (p))
	; )
	; (:action bad2	;; makes the goal false for no reason
	; 	:parameters ()
	; 	:precondition ()
	; 	:effect (not (q))
	; )
)
