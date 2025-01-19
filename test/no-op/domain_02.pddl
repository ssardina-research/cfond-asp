(define (domain nooptest)
	(:requirements :strips :non-deterministic)
	(:predicates
		(p)
		(q)
	)

	;; make q true or no-op
	(:action sq
		:parameters ()
		:precondition (p)
		:effect (oneof (q) (and))
	)
)