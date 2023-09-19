
(define (problem line-3)
  (:domain tireworld)
  (:objects l1 l2 l3 - location)
  (:init (vehicle-at l1)
    (road l1 l2)
    (road l2 l3)


    (spare-in l1)
    (spare-in l2)
    (spare-in l3)

    (fuel-in l1)
    (fuel-in l2)
    (fuel-in l3)

    (not-flattire)
    (not-empty)
)
  (:goal (vehicle-at l3)))
