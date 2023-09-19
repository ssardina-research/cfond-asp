(define (domain tireworld)
  (:requirements :typing :strips :non-deterministic)
  (:types location)
  (:predicates (vehicle-at ?loc - location)
	       (spare-in ?loc - location)
	       (road ?from - location ?to - location)
         (port ?loc - location)
	       (not-flattire))
  (:action move-car
    :parameters (?from - location ?to - location)
    :precondition (and (vehicle-at ?from) (road ?from ?to) (not-flattire))
    :effect (and 
		 (oneof (and (vehicle-at ?to) (not (vehicle-at ?from)))
			(and (vehicle-at ?to) (not (vehicle-at ?from)) (not (not-flattire))))))

  (:action changetire
    :parameters (?loc - location)
    :precondition (and (spare-in ?loc) (vehicle-at ?loc))
    :effect (and (not (spare-in ?loc)) (not-flattire)))

  (:action teleport
    :parameters (?loc - location)
    :precondition (not (and(vehicle-at? loc) (port? loc)))
    :effect (vehicle-at ?loc))
    )
