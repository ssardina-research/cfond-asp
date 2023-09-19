
(define (problem line-3)
  (:domain tireworld)
  (:objects l1 l2 l3 l4 - location)
  (:init (vehicle-at l1)
    (road l1 l2)
    (road l2 l3)
    (road l3 l4)

    (spare-in l1)
    (spare-in l2)
    (spare-in l3)
    (spare-in l4)

    (not-flattire)
)
(:goal (and (vehicle-at l4) (spare-in l3))
  )
)

