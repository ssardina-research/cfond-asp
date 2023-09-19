#script (python) 

from clingo import Number, String, Function

def get(val, default):
    return val if val != None else default

def main(prg):
    imin   = get(prg.get_const("imin"), Number(0))
    imax   = prg.get_const("imax")
    istop  = get(prg.get_const("istop"), String("SAT"))

    step, ret = 0, None
    

    while ((imax is None or step < imax.number) and
           (step == 0 or step < imin.number or (
              (ret and istop.string == "SAT" and not ret.satisfiable)))):
        
        parts = []
        if step > 0:
            parts.append(("step", [Number(step)]))
            prg.release_external(Function("query", [Number(step-1)]))
        else:
            parts.append(("base", []))
        parts.append(("check", [Number(step)]))
        prg.ground(parts)
        
        prg.assign_external(Function("query", [Number(step)]), True)
        
        ret = prg.solve()
        
        step = step+1
#end.

#program check(t).
#external query(t).