(define (domain example1)
  (:requirements :non-deterministic :typing)

(:predicates
	(p)
	(q)
	(r)
	(z)
)

(:action a
	:parameters ()
	:precondition (p)
	:effect (oneof (not (r)) (and ( not (p))( q)))
)

(:action b
	:parameters ()
	:precondition (not (p))
	:effect (z)
)

(:action c
	:parameters ()
	:precondition (not (r))
	:effect (z)
)
)
