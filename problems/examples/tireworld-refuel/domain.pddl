(define (domain tireworld)
  (:requirements :typing :strips :non-deterministic)
  (:types location)
  (:predicates (vehicle-at ?loc - location)
	       (spare-in ?loc - location)
           (fuel-in ?loc - location)
	       (road ?from - location ?to - location)
	       (not-flattire)
           (not-empty)
    )
  (:action move-car
    :parameters (?from - location ?to - location)
    :precondition (and (vehicle-at ?from) (road ?from ?to) (not-flattire) (not-empty))
    :effect (and 
		 (oneof 
            (and (vehicle-at ?to) (not (vehicle-at ?from)))
			(and (vehicle-at ?to) (not (vehicle-at ?from)) (not (not-flattire)))
            (and (vehicle-at ?to) (not (vehicle-at ?from)) (not (not-empty)))
            (and (vehicle-at ?to) (not (vehicle-at ?from)) (not (not-flattire)) (not (not-empty))))
            
        ))

  (:action changetire
    :parameters (?loc - location)
    :precondition (and (spare-in ?loc) (vehicle-at ?loc))
    :effect (and (not (spare-in ?loc)) (not-flattire)))

  (:action refuel
    :parameters (?loc - location)
    :precondition (and (fuel-in ?loc) (vehicle-at ?loc))
    :effect (not-empty)))

