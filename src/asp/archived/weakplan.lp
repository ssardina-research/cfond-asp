%*---------------------------------------------------------------------------------------------------------------
ASP based encoding for computing a weak plan.
---------------------------------------------------------------------------------------------------------------*%

%*---------------------------------------------------------------------------------------------------------------
- numStates (input). Upper bound on the number of states in a controller.
The total number of states in a controller will be numStates + 1.
---------------------------------------------------------------------------------------------------------------*%
#const numStates = 2.

%*---------------------------------------------------------------------------------------------------------------
:::Definition: State 
A controller state is modelled by terms state(0), state(1), ..., state(n) where n is the upper bound (i.e., numStates).
State 0 is reserved for the initial state and the highest number (i.e., numStates) is reserved for the goal state.
---------------------------------------------------------------------------------------------------------------*%
state(0..numStates).

% Set 0 as the initial state
initialState(0).

% set numStates as the goal state.
goalState(numStates).

%*---------------------------------------------------------------------------------------------------------------
:::GENERATION: A transition is a tuple (State, Action, Effect, State).
---------------------------------------------------------------------------------------------------------------*%
{transition(State, Action, Effect, State+1): state(State+1), actionEffect(Action, Effect)}=1 :- state(State), not goalState(State).

%*---------------------------------------------------------------------------------------------------------------
:::Auxiliary terms based on transitions.

- succesor(X,Y): Y is a succesor of X if there is a transition from X to Y.
---------------------------------------------------------------------------------------------------------------*%
successor(X, Y) :- transition(X, _, _, Y).
policy(State, Action) :- transition(State, Action, _, _).

%*---------------------------------------------------------------------------------------------------------------
:::GENERATION: The term holds(S, Var, Val) implies that variable Var has value Val in state S.

The constraint only allows at most one value per variable per state. The encoding only propagates negative effects, hence it is upto the solver to set the positive values of variables.
Note:- This is constrained by preconditions of actions (see the constraint on action precondition).
Note:- This may not be required, but it speeds up solving.
---------------------------------------------------------------------------------------------------------------*%
0 {holds(State,Variable,Value) : variableValue(Variable,Value)} 1 :- state(State), variable(Variable).

%*---------------------------------------------------------------------------------------------------------------
:::Constraints: Action precondition: (n, a) -> p(n) if p in prec(a)

P1. If a tuple (S, A) is in the policy and a variable Var has value Val in action A's precondition 
    then it should not be the case that Var does not have value Val in state S.
---------------------------------------------------------------------------------------------------------------*%
:- policy(State, Action), precondition(Action, Variable, Value), not holds(State, Variable, Value). % P1

%*---------------------------------------------------------------------------------------------------------------
:::Propagation of negative conditions.

N1. If an action deletes a value Val of a variable Var, then it should be the case that Var does not hold value Val in the next state resulting from this action. 
N2. If a variable Var does not hold a value Val in a state, then Var should not hold value Val in the next state unless an action is done whose effect sets value of Var to Val.
N3. If a variable Var does not hold a value Val in a state, then Var should not hold value Val in the next state if an effect does not add it, but its sibling adds it.
    This enforces that in this case the siblings yield a different state.

NOTE:: The use of not holds in implication increases the grounding speed but reduces the solving speed. Replacing implication with integrity constraint reduces grounding and increases solving time considerably.
---------------------------------------------------------------------------------------------------------------*%
not holds(State+1, Variable, Value) :- transition(State, Action, Effect, State+1), del(Action, Effect, Variable, Value). % N1
not holds(State+1, Variable, Value) :- not holds(State, Variable, Value), state(State), variableValue(Variable, Value), {transition(State, Action, Effect, State+1): add(Action, Effect, Variable, Value)} 0. % N2

%*---------------------------------------------------------------------------------------------------------------
:::Mutex (derived from SAS encoding). In any state, there should be at most one mutually exclusive variable value pairs.
---------------------------------------------------------------------------------------------------------------*%
:- mutexGroup(Group), state(State), not {holds(State, Variable, Value) : mutex(Group, Variable, Value)} 1.

%*---------------------------------------------------------------------------------------------------------------
:::Strong cyclic solution: Goal should be reachable from all states. This is specified by three constraints.

S1. Goal is reachable from the goal state.
S2. If goal is reachable from a state Y, then goal is reachable from all states X, such that Y is a successor of X.
S3. It should not be the case that there is a state from where goal is unreachable.
---------------------------------------------------------------------------------------------------------------*%
reachableG(State) :- goalState(State).  % S1
reachableG(State) :- successor(State, State+1), reachableG(State+1).  % S2
:- not reachableG(State), state(State).  % S3

%*---------------------------------------------------------------------------------------------------------------
:::Output. Show transition, holds, and policy.
---------------------------------------------------------------------------------------------------------------*%
#show transition/4.
% #show holds/3.
% #show policy/2.



% #heuristic policy(State, Action). [2, factor]
% #heuristic holds(State, Variable, Value). [2, factor]
% #heuristic policy(State, Action). [2, factor]

% compute the effects of the action sooner than later.
% TODO
% #heuristic  holds(State, Variable, Value): not goalState(State).  [2 * numStates - State, factor]
% #heuristic policy(State, Action): not goalState(State). [2*State+1, factor]

% #heuristic  holds(State-1, Variable, Value) : holds(State, Variable, Value).  [5*numStates - State +1, true]