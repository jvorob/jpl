# Janet Vorobyeva
# 2019.12

# (python3)
import clause as cls
import readline
import sys

VERSION = 0.1
VERBOSE = False

"""
Interpreter for jan prolog

Uses rules/terms/unification from clause.py

TODO:



TODO-EVENTUAL:
- Integrity check, all vars in step stack/rule stack should only be bound thru vars
  also within the stack
- Indexing: let Program do some smart filtering

"""


def dprint(*args):
    if VERBOSE:
        print(*args)



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

    def strAll(self):
        " Returns a string of all levels to root "

        msg = ""

        if self.prevStep is not None:
            msg = self.prevStep.strAll()

        msg = str(self) +"\n" + msg
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
        # check for end
        if tryRule is None:
            return None

        #see if we unify with tryclause
        rCopy = tryRule.copy()
        rCopy.setInstanceId(currStep.depth() + 1)

        succ, bindings = cls._tryUnify(rCopy.head, firstGoal)
        if succ:
            break

        # == unification failed, undo bindings
        for b in reversed(bindings):
            b[0].unbind() #unbind the variable
        #TODO: destroy rule somehow?


        # Get next rule to continue from
        tryRule, index = prog.getRule(index)



    # === We've successfully unified with the head of tryRule
    # Create a step to represent this

    #print("Succeeded with rule:", tryRule)
    #print(tryRule.body)

    newGoals = list(rCopy.body)
    remainingGoals = currStep.goals[1:]

    # need to create new step: store rule, index, update goal list
    newStep = ExecutionStep(currStep, 
            rCopy, index,
            bindings,
            newGoals + remainingGoals)

    return newStep



def outerInterp(state, prog):

    #Start from state, return an answer
    #If called repeatedly, should return all answers in order
    #If no more answers, returns None


    bookmark = None #for the current step, where do we leave off from
    # Update this each time we push/pop/take a step

    while True:
        # If we ever have an empty state (i.e. popped query), return None
        if state is None:
            return None

        # If we have empty goallist, it's from a prev answer, so need to pop
        if len(state.goals) == 0:
            # Pop: store bookmark to continue from & destroy the step
            bookmark = state.ruleIndex
            state = rewindStep(state)
            continue

        # ======= THERE IS YET WORK TO BE DONE

        # Try to make progress towards one of our goals
        nextState = TakeStep(state, prog, bookmark)

        # If no way to make progress forward, need to retry the currentStep
        if nextState is None:

            #We're instead retrying the current step, so load its bookmark and pop stack
            bookmark = state.ruleIndex
            state = rewindStep(state)
            continue
        

        #ELSE: we successfully took a step and made progress
        state = nextState
        bookmark = None #start from beginning for the next step

        #check if it's an answer (we return here, and discard on reentry)
        if len(state.goals) == 0:
            return state

        
        # We took a step, made progress, and aren't done yet
        continue





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


def parseQuery(querystring):
    " Parses out a query from the string. Throws on error "
    strm = cls.ParseStream("goal :-" + querystring)
    rule = cls._parseRule(strm)
    cls._chomp(strm)
    strm.assertNext(None)
    return rule





def fullInterp(program, querystring):
    queryRule = cls._parseRule(cls.ParseStream("goal :-" + querystring))
    firstStep = makeFirstStep(queryRule)

    def printBindings():
        for k,v in queryRule.bindings.items():
            print("{} = {}".format(k, v))


    curr = firstStep
    while True:
        nextStep = outerInterp(curr, program)

        if nextStep is None:
            print("no")
            break

        print("yes")
        print(queryRule.body) #TEMP?
        print(nextStep.strAll())
        printBindings()
        print("")
        curr = nextStep


def interactiveInterp(program):
    "Prints a prompt and responds to user queries"

    def printBindings():
        " print all bindings, then stop on the last one (no \\n) "
        lines = []
        for k,v in queryRule.bindings.items():
            lines.append("  {} = {}".format(k, v))

        print("\n".join(lines), end='')

    while True:
        #=== Get a valid query string
        try:
            queryStr = input("> ")
            if not queryStr.strip(): #skip blanks
                continue

            queryRule = parseQuery(queryStr)

        except EOFError:
            break
        except cls.ParseError as e:
            print(e)  #Parse error
            continue


        # === Ok, we got one:
        curr = makeFirstStep(queryRule)
        while True:
            nextStep = outerInterp(curr, program)

            if nextStep is None:
                print("no")
                break


            #= If we made some variable bindings: show them
            #= Then ask if user wants more answers
            done = True
            if len(queryRule.bindings)>0:
                printBindings()

                #print(queryRule.body) #TEMP?
                dprint(nextStep.strAll())

                
                # Check if user wants more answers
                response = input()
                if response.strip() != "": #non-whitespace means keep checking
                    done = False


            if done:
                print("\nyes\n")
                break #break out to query shell


            # Else continue with rest of answer
            curr = nextStep
            print("")




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

    prog = Program.ParseString("true. foo(X) :- bar(X).  bar(a):- true. bar(b):- true.")
    queryRule = cls._parseRule(cls.ParseStream("goal :- bar(X)."))
    firstStep = makeFirstStep(queryRule)


    a1 = outerInterp(firstStep, prog)

    print(a1.strAll())
    print(queryRule)

    a2 = outerInterp(a1, prog)
    print(a2.strAll())
    print(queryRule)

    a3 = outerInterp(a2, prog)
    print(a3)




def runFile(fname):
    try:
        with open(fname) as f:
            prog_text = f.read()
    except:
        print("Failed to read file '{}'".format(fname))
        exit(1)

    print("=== JPL {} ===". format(VERSION))
    print("Loaded program from {}".format(fname))

    try:
        prog = Program.ParseString(prog_text)
    except cls.ParseError as e:
        print("Failed to parse program")
        print(e)
        return

    interactiveInterp(prog)

def runDemo():
    print("=== JPL {} ===". format(VERSION))
    print("Running demo program:")
    for line in DEMO_PROGRAM.splitlines():
        print("    " + line)
    print()

    try:
        prog = Program.ParseString(DEMO_PROGRAM)
    except cls.ParseError as e:
        print("Failed to parse program")
        print(e)
        return

    interactiveInterp(prog)



DEMO_PROGRAM = """
true.
=(X,X).  % This needs to be defined manually
foo(X) :- bar(X).
bar(a).
bar(b).
% Try running `foo(X).`, or just `X.`
% Some notes: there is no 'occurs' check: Try not to make infinite recursion
% There are also no integers or things
"""



def printUsage():
    s = """
    Usage: {} [-h] [FILE]
    - With no args: runs a demo program
    - With an arg: tries to load a prolog program from file
    """
    print(s)
    exit(1);

def main():
    " Main entry point for normal operation "

    num_args = len(sys.argv) - 1
    
    if num_args == 0:
        runDemo()
    elif num_args > 1:
        printUsage()
    elif sys.argv[1] in ["-h", "--help", "-?"]:
        printUsage()

    else: #1 arg: treat as a file
        fname = sys.argv[1]

        runFile(fname)

    # Check the command line: 
    # if no args: demo prog
    # if help arg: printusage
    # if 1 arg: try load file
    # if many args: printusage




if __name__ == "__main__":

    #testStep()
    #testOuterInterp()
    main()
