%*---------------------------------------------------------------------------------------------------------------
ASP based encoding for computing a FOND controller, inspired by FondSat
---------------------------------------------------------------------------------------------------------------*%

%*---------------------------------------------------------------------------------------------------------------
- numStates (input). Upper bound on the number of states in a controller.

State 0 is reserved for the initial state and the highest number (i.e., numStates) is reserved for the goal state.
The total number of states in a controller will be numStates + 1.
---------------------------------------------------------------------------------------------------------------*%
#const numStates = 2.


% State declaration. This creates terms state(0), state(1), ..., state(n) where n is the upper bound (i.e., numStates).
state(0..numStates).

% Set 0 as the initial state
initialState(0).

% set numStates as the goal state.
goalState(numStates).


%*---------------------------------------------------------------------------------------------------------------
:::GENERATION: A metaPolicy is a tuple (State, ActionType). There should be one tuple per state.

Action Type: An action type is the name of an action (i.e., an action without its arguments).
    For example, given an action pick-from-table(b1), its action type is pick-from-table. 
    Nondeterministic planning actions are determinised by adding a suffix. 
    For example, the non-deterministic action put-on-block(b1, b1) with two nondeterministic effects, will have two determinised actions
    put-on-block_det_0(b1, b1), and put-on-block_det_1(b1, b1). The action types of these actions will be put-on-block_det_0 and put-on-block_det_1.

An example of a metaPolicy tuple is (0, put-on-block)
---------------------------------------------------------------------------------------------------------------*%
0 {metaPolicy(State, ActionType): actionType(ActionType)} 1 :- state(State), not goalState(State).


%*---------------------------------------------------------------------------------------------------------------
:::GENERATION: A policy is a tuple (State, Action),
   such that (State, ActionType) is in the metapolicy, where the type of action in the policy is of the correct type (as per the metapolicy).

The number of actions per state are equal to the number of nondeterministic effects of the underlying domain action.
For example, for metaPolicy tuple (0, put-on-block) and domain action put-on-block(b1, b1)
there should be two policy tuples (0, put-on-block_det_0(b1, b1)), and (0, put-on-block_det_1(b1, b1)).
Note: The generation only bounds the number of tuples per state and the action type. We require an additional constraint to include all siblings (constraint S1 below).
---------------------------------------------------------------------------------------------------------------*%
Z {policy(State, Action): actionType(ActionType, Action)} Z  :- metaPolicy(State, ActionType), numEffects(ActionType, Z).

%*---------------------------------------------------------------------------------------------------------------
:::GENERATION: A transition is a tuple (State, Action, State), such that (State, Action) is in the policy.

An action from a state yields one successor. However, the constraint allows multiple actions from a state to have the same successor state.
---------------------------------------------------------------------------------------------------------------*%
1 {transition(State, Action, NextState): state(NextState)} 1 :- policy(State, Action).

%*---------------------------------------------------------------------------------------------------------------
:::GENERATION: The term holds(S, Var, Val) implies that variable Var has value Val in state S.
   The constraint only allows at most one value per variable per state.
   The encoding only propagates negative effects, hence it is upto the solver to set the positive values of variables.

   Note:- This is constraint by preconditions of actions (see the constraint on action precondition).
   Note:- The initial state is modelled as which variable values do not hold,
          whereas the goal state is modelled as which variable values hold in the goal state.
---------------------------------------------------------------------------------------------------------------*%
0 {holds(State,Variable,Value) : variableValue(Variable,Value)} 1 :- state(State), variable(Variable).

%*---------------------------------------------------------------------------------------------------------------
:::Auxilary terms: We define the following auxiliary terms.

successor(X,Y): A state Y is a successor of a state X if there is a transition from X to Y.
---------------------------------------------------------------------------------------------------------------*%
successor(X, Y) :- transition(X, _, Y).


%*---------------------------------------------------------------------------------------------------------------
:::Constraints on transitions. We specify two syntactic constraints on valid transition tuples.

T1. An action can only be applied at most once from a given state.
S1. A policy should account for all deterministic siblings of an action.
    That is, if (S, A1) is in the policy and A2 is a sibling of A1 then it should not be the case that (S, A2) is not in the policy.
---------------------------------------------------------------------------------------------------------------*%
:- state(State), action(Action), not 0 {transition(State, Action, _)} 1.  % T1
:- policy(State, Action1), sibling(Action1, Action2), not policy(State, Action2). % S1

%*---------------------------------------------------------------------------------------------------------------
:::Symmetry breaking based on directed graphs.
    Symmetry breaking puts constraints on how nodes are connected. 
    The constraint is (ni , nj ) -> k≤i \/ (nk , nl), where j > 1, l=j-1, and ni , nj , nl are not goal states.
    Intuition is that a state ni should connect to ni+l only if states nj where j ≤ i are unavailable.
---------------------------------------------------------------------------------------------------------------*%
% :- successor(I, J), {successor(K, J-1):state(K), state(J-1), not goalState(J-1), K <= I} 0, state(I), state(J),  not goalState(I), not goalState(J), J>1.

% %%Experimental%
% % :- transition(S, A1, J1), transition(S, A2, J2), sibling(A1, A2), precedence(A1, A2), J2 < J1, not goalState(J1), J2 > S.
% % :- transition(S, A1, J1), J1 = S+2, not goalState(J1), 1 {transition(S, A2, J2): sibling(A1, A2), precedence(A1, A2), J2<J1, J2>S}.
% % :- 1 {transition(S, A1, S+2): not goalState(S+2), transition(S, A2, S+1), not goalState(S+1)}, precedence(A1, A2).
% % :- 1 {transition(S, A1, S+3): not goalState(S+3), transition(S, A2, S+2), not goalState(S+2)}, precedence(A1, A2).

% % :- 1 {transition(S, A1, J1): transition(S, A2, J2), not goalState(J1), not goalState(J2), J1>S, J2>S, J2 < J1}, precedence(A1, A2).
% :- transition(S, A1, J1), J1>S, not goalState(J1), 1 {transition(S, A2, J2): J2<J1, J2>S, not goalState(J2)}, precedence(A1, A2).

%*---------------------------------------------------------------------------------------------------------------
:::Action precondition: (n, a) -> p(n) if p in prec(a)
    If a tuple (S, A) is in the policy and a variable Var has value Val in action A's precondition 
    then it should not be the case that Var does not have value Val in state S.
---------------------------------------------------------------------------------------------------------------*%
:- policy(State, Action), precondition(Action, Variable, Value), not holds(State, Variable, Value).


%*---------------------------------------------------------------------------------------------------------------
:::Propagation of negative conditions.

N1. If an action deletes a value Val of a variable Var, then it should be the case that Var does not hold value Val in the next state resulting from this action. 
N2. If a variable Var does not hold a value Val in a state, then Var should not hold value Val in the next state unless an action is done that sets value of Var to Val.
N3. If a variable Var does not hold a value Val in a state, then Var should not hold value Val in the next state if an action does not add it, but its sibling adds it.
    This enforces that in this case the siblings yield a different state.
---------------------------------------------------------------------------------------------------------------*%
not holds(NextState, Variable, Value) :- transition(_, Action, NextState), del(Action, Variable, Value). % N1
not holds(NextState, Variable, Value) :- not holds(State, Variable, Value), variableValue(Variable, Value), successor(State, NextState), {transition(State, Action, NextState): add(Action, Variable, Value)} 0. % N2
not holds(NextState, Variable, Value) :- not holds(State, Variable, Value), variableValue(Variable, Value), transition(State, Action, NextState), not add(Action, Variable, Value), sibling(Action, SiblingAction), add(SiblingAction, Variable, Value).

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
reachableI(State) :- initialState(State).  % Initial state is reachable from start
reachableI(NextState) :- successor(State, NextState), reachableI(State).

reachableG(State) :- goalState(State).  % S1
reachableG(State) :- successor(State, NextState), reachableG(NextState).  % S2
:- reachableI(State), not reachableG(State).  % S3

:- not reachableG(S2), state(S2), 1 {reachableG(S1): not goalState(S1), S1 > S2}.
:- successor(I, J), {successor(K, J-1):state(K), state(J-1), not goalState(J-1), K <= I} 0, state(I), state(J),  not goalState(I), not goalState(J), J>1.

%% Force controller
% :- not transition(0,"move-car_DETDUP_1(l1,l2)",1), not transition(1,"changetire(l2)",2).
% :- not transition(0,"move-car_DETDUP_1(l1,l2)",2).

% not holds
% notHolds(State, Variable, Value) :- not holds(State, Variable, Value), state(State), variableValue(Variable, Value).


%
% #show metaPolicy/2.
#show transition/3.
#show holds/3.

#show state/1.
% #show notHolds/3.
% #show policy/2.
% #show reachableG/2.

