(define (domain simple-domain)
  (:requirements :non-deterministic)
  (:predicates (s0) (s1) (s2) (s3) (s4) (s5) (s6) (s7) (s8) (s9) (s10) (g))
  (:action a1
    :parameters ()
    :precondition (s0)
    :effect (and (not (s0)) (s1) )
  )
  (:action a2
    :parameters ()
    :precondition (s1)
    :effect (and (not (s1)) (s2) )
  )
  (:action a3
    :parameters ()
    :precondition (s2)
    :effect (and (not (s2)) (s3) )
  )
  (:action a4
    :parameters ()
    :precondition (s3)
    :effect (oneof
        (and (not (s3)) (s4) )
        (and (not (s3)) (s7) ))
  )
  (:action a5
    :parameters ()
    :precondition (s4)
    :effect (oneof
        (and (not (s4)) (s5) )
        (and (not (s4)) (s6) ))
  )
    (:action a7
    :parameters ()
    :precondition (s6)
    :effect (and (not (s6)) (s2) )
  )
    (:action a6
    :parameters ()
    :precondition (s5)
    :effect (and (not (s5)) (g) )
  )
    (:action a8
    :parameters ()
    :precondition (s7)
    :effect (and (not (s7)) (s8) )
  )
    (:action a9
    :parameters ()
    :precondition (s8)
    :effect (oneof
        (and (not (s8)) (s10) )
        (and (not (s8)) (s9) ))
  )
    (:action a10
    :parameters ()
    :precondition (s9)
    :effect (and (not (s9)) (s7) )
  )
      (:action a11
    :parameters ()
    :precondition (s10)
    :effect (and (not (s10)) (g) )
  )
)
