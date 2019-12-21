import clause as cls

"""
Interpreter for jan prolog

Uses rules/terms/unification from clause.py

TODO:
- Goal list / eval step (+pretty print)
- Outer interp
- Parse goal? (how to represent goal)
- Pre-unify



TODO-EVENTUAL:
- Distinguish between instances of variables
- Integrity check, all vars in step stack/rule stack should only be bound thru vars
  also within the stack
- Indexing: let Program do some smart filtering

"""



class Program:
    " Small abstraction around a list of rules"

    def __init__(self, rules):
        self.rules = rules
        

    @classmethod
    def ParseString(_class, s):
        strm = cls.ParseStream(s)

        rules = []
        while True:
            rule = cls._parseRule(strm)
            if rule is None:
                break

            rules.append(rule)

        return Program(rules)

    
    def getRule(self, bookmark = None):
        """ Returns (rule, bookmark).
        Calling getRule with the same bookmark will yield the next rule
        When no more available, returns (None, bookmark)
        """

        if bookmark is None:
            bookmark = 0

        if bookmark >= len(self.rules):
            return (None, bookmark)

        #bookmark will be the index of the next rule to return
        return (self.rules[bookmark], bookmark + 1)


    def __repr__(self):
        msg = ""
        msg += "Program:\n "
        msg += "\n ".join(str(r) for r in self.rules)

        return msg




class ExecutionStep:
    """ Represents last completed step in the execution:

    Holds past:
    - What was the previous step before this one

    Holds what happened in current step:
    - which clause did we just use?
    - which bindings did we just make?
    
    Holds state:
    - what is our current list of goals

    """


    def __init__(self, prevStep, currRule, ruleIndex, bindingsMade, goalList):
        self.prevStep = prevStep #is None for first query
        self.rule = currRule
        self.ruleIndex = ruleIndex #used as "Bookmark" into Program
        self.bindings = bindingsMade
        self.goals = goalList


    def depth(self):
        if self.prevStep is None:
            return 0
        else:
            return 1 + self.prevStep.depth()


    def __repr__(self):
        msg = ""
        msg += "<Step {}, ".format(self.depth())
        msg += "R{}, ".format(self.ruleIndex)
        msg += "Goals: {}, ".format(self.goals)
        msg += "Bindings: {}, ".format(self.bindings)


        return msg



def TakeStep(currStep, prog, startIndex = None):
    """
    try to take a step forward
    (can be told where to resume from (startIndex), use None for no restriction)
    If able to take a single step, return the new step you created
    If no rule matches, return None
    """

    #Get our goal clause
    assert len(currStep.goals) > 0, "ERROR: must only TakeStep when goals avaiable"
    firstGoal = currStep.goals[0]
    
    #Find a matching head clause
    tryRule, index = prog.getRule(startIndex) #get rule, and index to continue from

    # === Loop over rules in the program until one works or we run out
    while True:

        #print("Trying rule:", tryRule)

        #see if we unify with tryclause
        r = tryRule.copy()
        succ, bindings = cls._tryUnify(r.head, firstGoal)
        if succ:
            break

        # == unification failed, undo bindings
        for b in reversed(bindings):
            b[0].unbind() #unbind the variable
        #TODO: destroy rule somehow?


        # Get next rule to continue from
        tryRule, index = prog.getRule(index)

        # check for end
        if tryRule is None:
            return None


    # === We've successfully unified with the head of tryRule
    # Create a step to represent this

    print("Succeeded with rule:", tryRule)
    print(tryRule.body)

    newGoals = list(tryRule.body)
    remainingGoals = currStep.goals[1:]

    # need to create new step: store rule, index, update goal list
    newStep = ExecutionStep(currStep, 
            tryRule, index,
            bindings,
            newGoals + remainingGoals)

    return newStep



#def outerInterp(state):
#
#    #Start from state, return an answer
#    #If called repeatedly, should return all answers in order
#    #If no more answers, returns None
#
#
#    while True:
#        # If we ever have an empty state (i.e. popped query), return None
#        if state is None:
#            return None
#
#        # If we have empty goallist, it's from a prev answer, so need to pop
#        if len(state.goals) == 0:
#            #TODO: pop last step, since we've already seen that answer
#            continue
#
#
#        # Try to make progress towards one of our goals
#        nextState = TakeStep(state)
#
#        # If no way to make progress, pop stack
#        if nextState is None:
#            #TODO: pop
#            continue
#        
#
#        #ELSE: we successfully took a step and made progress
#        state = nextState
#
#        #check if it's an answer (we return here, and discard on reentry)
#        if len(state.goals) == 0:
#            return state
#
#        
#        # We took a step, made progress, and aren't done yet
#        continue





# ============================================================
#
#                           HELPERS?
#
# ============================================================

def makeFirstStep(queryRule):
    " Makes a trivial ExecutionStep from the body of a Rule "

    step = ExecutionStep(
            None,             # No Prev step
            queryRule, None,  # Rule, no bookmark index
            [],               # No bindings
            queryRule.body    # Goal list is just body
            );
    return step


def rewindStep(step):
    " Undoes bindings, returns the previous step"

    assert step is not None, "Don't rewind empty step"

    for b in reversed(step.bindings):
        b[0].unbind()

    return step.prevStep


# ============================================================
#
#                 MANUAL TESTING SHENANIGANS
#
# ============================================================

def testStep():

    prog = Program.ParseString("true. foo(X) :- bar(X).  bar(a) :- false. bar(b) :- true.")

    queryRule = cls._parseRule(cls.ParseStream("goal :- bar(X)."))
    firstStep = makeFirstStep(queryRule)

    print(firstStep)
    s2 = TakeStep(firstStep, prog)
    print(s2)
    s3 = TakeStep(s2, prog)
    print(s3)

    assert s3 is None, "UHH your test is broken"

    print ("step 3 failed")
    print ("retrying step 2")

    bookmark = s2.ruleIndex
    firstStep = rewindStep(s2)
    s2_2 = TakeStep(firstStep, prog, bookmark)
    print(s2_2)
    s3_2 = TakeStep(s2_2, prog)
    print(s3_2)

    print(queryRule)


def testOuterInterp():

    prog = Program.ParseString("foo(X) :- bar(X).  bar(a).")

    print(prog)


if __name__ == "__main__":
    print("Testing in engine.py")

    testStep()
    #testOuterInterp()
