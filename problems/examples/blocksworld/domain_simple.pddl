(define (domain blocks-domain)
  (:requirements :non-deterministic :equality :typing)
  (:types block)
  (:predicates (holding ?b - block) (emptyhand) (on-table ?b - block) (on ?b1 ?b2 - block) (clear ?b - block))

  (:action pick-from-table
    :parameters (?b - block)
    :precondition (and (emptyhand) (clear ?b) (on-table ?b))
    :effect ( and (holding ?b) (not (emptyhand)) (not (on-table ?b)))
  )


   (:action put-on-block
    :parameters (?b1 ?b2 - block)
    :precondition (and (holding ?b1) (clear ?b2))
    :effect (oneof (and (on ?b1 ?b2) (emptyhand) (clear ?b1) (not (holding ?b1)) (not (clear ?b2)))
                   (and (on-table ?b1) (emptyhand) (clear ?b1) (not (holding ?b1))))
  )
)
