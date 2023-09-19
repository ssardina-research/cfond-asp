(define (domain example2)
  (:requirements :typing)

(:predicates
	(p)
	(q)
    (r)
)

(:action a
	:parameters ()
	:precondition (not (p))
	:effect (p)
)

(:action b
	:parameters ()
	:precondition (not (q))
	:effect (q)
)

(:action c
	:parameters ()
	:precondition (and (p) (q))
	:effect (r)
)
)
