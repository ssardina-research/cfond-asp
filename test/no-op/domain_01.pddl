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
