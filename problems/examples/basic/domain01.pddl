(define (domain simple-domain)
  (:requirements :non-deterministic :typing)
  (:types block)
  (:predicates (holding ?b - block) (emptyhand) (on-table ?b - block) (on-destination ?b1 - block))
  (:action pick-up
    :parameters (?b1 - block)
    :precondition (and (emptyhand) (on-table ?b1))
    :effect (and (holding ?b1) (not (emptyhand)) (not (on-table ?b1)))
  )

  (:action put-down
    :parameters (?b - block)
    :precondition (holding ?b)
    :effect (
    oneof
    (and (on-table ?b) (emptyhand) (not (holding ?b)))
    (and (on-destination ?b) (emptyhand) (not (holding ?b))))
  )
)
