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
	(:action snp
		:parameters ()
		:precondition (p)
		:effect (not (p))
	)
)
