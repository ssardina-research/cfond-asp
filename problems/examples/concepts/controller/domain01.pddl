(define (domain example1)
  (:requirements :non-deterministic :typing)

(:predicates
	(p)
	(q)
	(r)
	(z)
    (g)
)

(:action a
	:parameters ()
	:precondition (z)
	:effect (oneof (and (not (r))(p)) (and (not (r))(q)))
)

(:action b
	:parameters ()
	:precondition (not (r))
	:effect (g)
)

(:action c
	:parameters ()
	:precondition (not (r))
	:effect (g)
)
)
