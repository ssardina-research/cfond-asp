(define (domain example2)

(:requirements :non-deterministic)

(:predicates
	(p)
	(r)
	(z)
)

(:action a
	:parameters ()
	:precondition (p)
	:effect (not (r))
)

(:action b
	:parameters ()
	:precondition (not (p))
	:effect (z)
)

(:action c
	:parameters ()
	:precondition (not (r))
	:effect ( and (z) (not p))
)
)
