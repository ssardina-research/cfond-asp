(define (problem bw_11_11)
  (:domain blocks-domain)
  (:objects b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 - block)
  (:init (emptyhand) (on b1 b5) (on b2 b6) (on b3 b8) (on-table b4) (on b5 b7) (on b6 b10) (on-table b7) (on b8 b9) (on b9 b1) (on b10 b3) (on-table b11) (clear b2) (clear b4) (clear b11))
  (:goal (and (emptyhand) (on b1 b6) (on b2 b11) (on b3 b8) (on b4 b1) (on b5 b9) (on b6 b3) (on b7 b10) (on-table b8) (on b9 b7) (on-table b10) (on b11 b4) (clear b2) (clear b5)))
)
