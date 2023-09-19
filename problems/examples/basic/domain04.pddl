(define (domain simple)
  (:requirements :non-deterministic)
  (:predicates (p) (q))

    (:action step1
    :parameters ()
    :precondition (not (q))
    :effect (q)
  )

    (:action step2
    :parameters ()
    :precondition (q)
    :effect (p)
  )


)
