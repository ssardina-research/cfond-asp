(define (domain simple)
  (:requirements :non-deterministic)
  (:predicates (p) (q) (r))
  
  (:action reset
    :parameters ()
    :precondition (p)
    :effect (not (p))
  )

    (:action finish
    :parameters ()
    :precondition (and (p) (q))
    :effect (r)
  )

  (:action try
    :parameters ()
    :precondition (and (not (p)) (not (q)))
    :effect (
    oneof
    (and (p) (not (q)))
    (and (p) (q) ))
  )
)
