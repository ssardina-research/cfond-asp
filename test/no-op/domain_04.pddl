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

	;; make irrelevant proposition false - will be deleted
	(:action act2
		:parameters ()
		:precondition (p)
		:effect (not (r))
	)

	;; make irrelevant proposition false but algo get the goal - will not be deleted
	(:action act2
		:parameters ()
		:precondition (p)
		:effect (and (q) (not (r)))
	)

)