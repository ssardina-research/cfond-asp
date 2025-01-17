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
