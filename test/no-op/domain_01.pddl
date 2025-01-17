(define (domain nooptest)
	(:requirements :strips)
	(:predicates
		(p)
		(q)
	)

	;; Action to move while being on the beam
	(:action sq
		:parameters ()
		:precondition (p)
		:effect (q) 
	)
)
