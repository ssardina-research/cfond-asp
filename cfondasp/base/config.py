DETERMINISTIC_ACTION_SUFFIX = "_DETDUP_"    # important that includes the underscores (or they will be added by the determinizer automatically and regular expression wont work!)
ASP_EFFECT_COUNT_TERM = "numEffects"
ASP_VARIABLE_TERM = "variable"
ASP_VARIABLE_ATOM_TERM = "variableValue"
ASP_MUTEX_GROUP_TERM = "mutexGroup"
ASP_MUTEX_TERM = "mutex"
ASP_HOLDS_TERM = "holds"
ASP_INITIAL_STATE_TERM = "initialState"
ASP_GOAL_STATE_TERM = "goalState"
ASP_GOAL_TERM = "goal"
ASP_ACTION_NAME_TERM = "actionName"
ASP_ACTION_TERM = "action"
ASP_PREC_TERM = "precondition"
ASP_ACTION_EFFECT_TERM = "actionEffect"
ASP_EFFECT_TERM = "e"
ASP_ADD_TERM = "add"
ASP_DEL_TERM = "del"
ASP_NDSIZE_TERM = "maxND"
ASP_AFFECTS_TERM = "affects"
ASP_ACTION_TYPE_TERM = "actionType"
ASP_SIBLING_TYPE_TERM = "siblingType"
ASP_SIBLING_TERM = "sibling"
ASP_RELEVANT_ACTION_TERM = "relevant"
ASP_COMPATIBLE_ACTION_TERM = "compatible"
ASP_CLINGO_OUTPUT_PREFIX = "clingo_out_"
ASP_OUT_LINE_END = "$END$"
ASP_OUT_DIVIDER = "--------"

FILE_INSTANCE = "instance.lp"   # asp encoding for finding strong/strong-cyclic solutions
FILE_INSTANCE_WEAK = "instance_weak.lp" # asp encoding for finding weak plans
FILE_WEAK_PLAN_OUT = "weak_plan.out"    # file to drop Clingo output for weak plan solving
FILE_BACKBONE = "backbone.lp"  # file to drop Clingo output for weak plan solving

CLINGO_BIN = "clingo"
DETERMINISER_BIN = "fond-utils" # not really used anymore, used via library API
TRANSLATOR_BIN = "translate.py"

DEFAULT_MODEL = "fondsat"  # strong-cyclic fondsat-type encoding
FD_INV_LIMIT = 300

PYTHON_MINOR_VERSION = 10   # minimum python version required

FILE_CONTROLLER_WEAK = "controller-weak.lp"
