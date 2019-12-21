# //python 3
import re


"""
Defines Clauses, Terms, Rules
Will be used by higher-level modules like parser (creates rules),
And the main interpreter (executes queries using rules and terms and things)

NOTES/TODO list:

TODO:


TODO-EVENTUAL:
- List pretty-print
- List parse
- less-verbose printer (add verbose flag to terms)


A Term is a variable or a functor (with children or without (if atom))
Variables are a string key and a context (either the parent rule or a CTX object)
A clause is just a term

A rule is a head clause, followed by a list of body clauses
+ a context (which stores variables defined in that rule's clauses)

NOTE: Creation conventions:
- Variables are created WITHOUT A CONTEXT
- HOWEVER: if a variable is derefed or bound without a context, we raise an exception
- Rules must be created with terms already made,
- Rule constructor binds all vars in its clauses
"""


# ============================================================
#
#                 OBJECTS (Terms/Rules)
#
# ============================================================

class Term:
    """ Represents a var or functor (or atom if functor/0) 
Vars should be bound to a rule instance (that's the binding context)
    ABSTRACT: don't instantiate
    """

    def isVar(self):
        return isinstance(self, Var)


    # applies function to self & each subterm within self
    # applies to vars but doesn't deref them
    # doesn't return anything rn
    def shallowMap(self, mapfun):
        mapfun(self) # functor overrides this to recurse on children


    def copy(self):
        " Copies tree, stops at vars (copy's vars are unbound)"
        assert False, "Don't call copy on Term class"


    def __repr__(self):
        return self.safeStr()

    def safeStr(self, depth=10):
        " Stringifies term, limits depth"
        if depth == 0:
            return "..."

        else:
            return "(Blank Term)"



class Functor(Term):

    def __init__(self, token, subterms):
        super().__init__()
        self.token = token
        self.subterms = list(subterms)

    # applies function to self & each subterm within self
    # applies to vars but doesn't deref them
    # doesn't return anything rn
    def shallowMap(self, mapfun):
        mapfun(self)
        for child in self.subterms:
            child.shallowMap(mapfun)


    def copy(self):
        " Copies tree, stops at vars (copy's vars are unbound)"
        childCopies = [s.copy() for s in self.subterms]
        return Functor(self.token, childCopies)


    def __repr__(self):
        return self.safeStr()


    def safeStr(self, depth=10):
        if depth == 0:
            return "..."

        if len(self.subterms) == 0:
            return self.token

        subtermstr = ", ".join(x.safeStr(depth-1) for x in self.subterms)
        return "{}/{}({})".format(self.token, len(self.subterms), subtermstr)


    def shortname(self):
        " string like functor/3"
        return "{}/{}".format(self.token, len(self.subterms))


class Var(Term):
    def __init__(self, token):
        " token is var name "
        super().__init__()
        self.token = token

        self.context = None #Starts uninitialized


    def copy(self):
        " Copies tree, stops at vars (copy's vars are unbound)"
        return Var(self.token)

    def deref(self):
        " Recursively dereferences self until reach nonvar or unbound var "
        " If unbound, returned value is var"

        assert isinstance(self.context, Rule), "ERROR: deref context-less Var"

        if self.token not in self.context.bindings:
            return self # we're deepest unbound, return self

        # we're bound, deref once
        binding = self.context.bindings[self.token]


        if not binding.isVar(): # hit a concrete value, done
            return binding
        else:
            # If hit var, continue
            assert binding != self #this shouldn't happen, also we shouldn't get loops

            return binding.deref()



    def bindTo(self, term):
        " Binds self <= term, returns the var instance which got changed "

        assert isinstance(self.context, Rule), "ERROR: binding context-less Var"

        # NOTE: binding is set on deepest var in chain
        # Ensures non-loops (I think), and ensures undoing preserves older structure

        # Get deepest bound var
        # NOTE: if deepvar is a Functor, then that means self was already bound
        deepvar = self.deref() 
        assert deepvar.isVar(), "Can't re-bind an already-bound var"

        # make binding & return the var that was updated
        deepvar.context.bindings[deepvar.token] = term
        return deepvar 


    def unbind(self):
        " removes whatever binding this currently holds at this level (doesn't deref) "

        assert isinstance(self.context, Rule), "ERROR: unbinding context-less Var"

        # We don't have to be bound to a concrete value, but we shouldn't be a root unbound
        assert self.token in self.context.bindings, "ERROR: unbinding root unbound var"

        del self.context.bindings[self.token]


    def __repr__(self):
        return self.safeStr()

    def safeStr(self, depth=10):
        if depth == 0:
            return "..."

        # show context-less vars
        if not isinstance(self.context, Rule):
            return "(${}!!)".format(self.token)


        # Show unbound vars
        boundval = self.deref()
        if isinstance(boundval, Var):
            return "(${}={})".format(self.token, boundval.token)

        # Else, we have a functor
        return "(${}={})".format(self.token,boundval.safeStr(depth-1))


class Rule:
    " Represents an instance of a rule (e.g. multiple invocations make multiple rule objs) "

    def __init__(self, headClause, bodyClauses):
        self.bindings = {}
        self.head = headClause
        self.body = bodyClauses

        def reparent(term):
            if term.isVar():
                term.context = self

        # Set self as context for all vars in head & body clauses
        self.head.shallowMap(reparent)
        for bclause in self.body:
            bclause.shallowMap(reparent)



    def copy(self):
        " Makes a copy: all variables in copy are unbound "

        h2 = self.head.copy()
        b2 = [b.copy() for b in self.body]

        return Rule(h2, b2)


    def __repr__(self):
        msg = ""
        msg += "<Rule:\n"
        msg += "  HD: {}\n".format(str(self.head))
        msg += "  BODY: {}\n".format(", ".join(str(b) for b in self.body))
        msg += "  Vars:{}>".format(self.bindings)
        return msg

# ============================================================
#
#                        UNIFICATION 
#
# ============================================================


# NOTE: How do we store undo entries?
# (boundVar, "nice string")


def unify(c1, c2):
    """ 
Unifies clause1 onto clause2
Returns list of bindings made
If fails, undoes its own bindings, and returns None

(for reference, c1 is the new clause (think it might not matter actually))
MUST ONLY BE CALLED ON INITIALIZED TERMS
"""
    pass



def _tryUnify(c1, c2):
    """
Helper: attempts to unify clause1 onto clause2
Returns (success, bindingsMade)
Doesn't attempt to undo

#c1 is the newer clause, will be bound to c2 if both are vars
    """


    #C is for clause, d is for dereferenced, b is for bound?

    #dereference them (if we bind them, we want to work with the deepest level of var pointer)
    d1, d2 = c1, c2
    if d1.isVar():
        d1 = d1.deref()
    if d2.isVar():
        d2 = d2.deref()


    # Check if theyre bound (var is bound if it derefs to a nonvar)
    b1, b2 = not d1.isVar(), not d2.isVar()


    # ======== Switch on functor/var

    if b1 and b2: #===== both are bound (functors):
        if d1.token != d2.token:
            print("Unify failed: {} & {} name mismatch".format(d1.shortname(), d2.shortname()))
            return (False, [])

        if len(d1.subterms) != len(d2.subterms):
            print("Unify failed: {} & {} arity mismatch".format(d1.shortname(), d2.shortname()))
            return (False, [])

        else: #recursively unify children
            bindings = []
            for a,b in zip(d1.subterms, d2.subterms):
                (succ, sub_binds) = _tryUnify(a,b)
                bindings += sub_binds

                if not succ:
                    return False, bindings

            return True, bindings
                    

    else: #=== At least one is a variable, need to do a binding

        if    not b1 and not b2: #both unbound, bind newer clause to older
            bindee, target = d1, d2

        elif  not b2 and b1: #only b2 is var, bind it
            bindee, target = d2, d1
    
        elif  not b1 and b2: #only b1 is var, bind it
            bindee, target = d1, d2
        else:
            raise Exception("ERROR: SHOULDNT GET HERE")


        #Need to store which var the binding was made on,
        #Also want to have a descriptive string for it
        binding = ( bindee, "{} <= {}".format(str(bindee), str(target)))

        bindee.bindTo(target) # (it'll do the deref chain twice, but whatever)

        return (True, [binding])




# ============================================================
#
#                          PARSER
#
# ============================================================


class ParseStream:
    " Represents state of the parser through its input "

    def __init__(self, instr):
        self.str = instr
        self.offset = 0

    def peek(self):
        " returns next char or None "
        off = self.offset
        return self.str[off] if off < len(self.str) else None

    def drop(self):
        self.offset += 1

    def assertNext(self, c):
        if self.peek() != c:
            raise Exception("ERROR: expected next char '{}', at {}".format(c, str(self)))

    def raiseErr(self, error=""):
        raise Exception("ERROR: {}, at {}".format(error, str(self)))

    def __repr__(self):
        context = self.str[self.offset: self.offset + 50]
        if(len(self.str) >= self.offset + 50):
            context += "..."

        return "<pos:{}, text:'{}'>".format(self.offset, context)




def _chomp(strm):
    while strm.peek() in [' ', '\n', '\t']:
        strm.drop()

def _parseIdentChar(strm):
    "Consumes one char of identifier of [=?+*A-Za-z0-9_], else return None"
    # DOESNT CHOMP
    c = strm.peek()
    if ((c is not None)) and re.match(r'[\-=?+*A-Za-z0-9_]', c):
        strm.drop()
        return c

    else:
        return None

def _parseIdent(strm):
    "Snags an identifier of identChars, or None if doesn't match"
    # DOESNT CHOMP

    result = ""
    while True:
        c = _parseIdentChar(strm)
        if c is None:
            break

        result += c

    if result == "":
        return None

    return result


def _parseTerm(strm):
    " We're expecting a term "

    _chomp(strm)

    #TODO:
    # parens?

    c = strm.peek()

    if c.isupper():
        return _parseVar(strm)
    elif c.islower():
        return _parseFunctor(strm)


    # Else: neither
    strm.raiseErr("expecting Term, got non-alpha char")


def _parseVar(strm):
    " We're at an uppercase letter: parse off a char"

    ident = _parseIdent(strm)
    if ident is None:
        strm.raiseErr("Failed to get ident in _parseVar")

    return Var(ident)

def _parseFunctor(strm):
    " We're at a lowercase letter: parse off a functor and subterms "

    head_ident = _parseIdent(strm)
    if head_ident is None:
        strm.raiseErr("Failed to get ident in _parseFunctor")


    # now need to parse subterms
    _chomp(strm)

    c = strm.peek()

    # if '(', parse subterms, else is atom
    if c != '(':
        return Functor(head_ident, [])


    children = []
    # Else: we're in the child subterms
    strm.drop() # drop the '('
    while True:
        _chomp(strm)

        child = _parseTerm(strm)
        children.append(child)

        #Now: check if continue ',' or end ')'
        _chomp(strm)
        c = strm.peek()

        if c == ',':
            strm.drop() # drop the ','
            continue

        if c == ')':
            strm.drop() # drop the ')'
            break

        strm.raiseErr("Parsing functor subterms, expected ',' or ')'")

    # We've parsed all children
    return Functor(head_ident, children)


# === Rule parser


def _parseRule(strm):
    """ Parse a rule of the form TERM. or TERM:- BODY, BODY, ... , .
    returns None if at EOF
    """

    # check if has head
    _chomp(strm)
    c = strm.peek()
    if c is None:
        return None
    

    head = _parseTerm(strm)

    # check if has body
    _chomp(strm)
    c = strm.peek()

    # if '.' then it's a fact, if ":-" then it has a body
    if c == '.':
        strm.drop()
        return Rule(head,[])

    elif c != ':':
        strm.raiseErr("Expected '.' or ':-' after rule head")

    #else: we're in a "head :- b1, ..., bn ." rule
    body = []
    strm.drop() # drop the ':'
    strm.assertNext('-')
    strm.drop() # drop the '-'

    while True:
        _chomp(strm)
        b = _parseTerm(strm)
        body.append(b)

        #Now: check if continue ',' or end '.'
        _chomp(strm)
        c = strm.peek()

        if c == ',':
            strm.drop() # drop the ','
            continue

        if c == '.':
            strm.drop() # drop the '.'
            break

        strm.raiseErr("Parsing rule body clauses, expected ',' or '.'")


    return Rule(head, body)





# ============================================================
#
#                 MANUAL TESTING SHENANIGANS
#
# ============================================================


def testSimpleTerms():
    f1 = Functor("a",[])

    v1 = Var("X")
    v2 = Var("Y")
    v3 = Var("Y")

    f2 = Functor("foo",[f1,v1,v2,v3])

    r = Rule(f2, [v1, f1])

    v1.bindTo(f1)
    v3.bindTo(v1)


    print(f2)
    print(r)

def testCopy():
    f1 = Functor("a",[])

    v1 = Var("X")
    v2 = Var("Y")
    v3 = Var("Y")

    f2 = Functor("foo",[f1,v1,v2,v3])

    r = Rule(f2, [v1, f1])

    #v1.bindTo(f1)
    v3.bindTo(v1)


    r2 = r.copy()
    # Bind X = a
    r2.head.subterms[1].bindTo(r2.head.subterms[0])

    print(r)
    print(r2)


def testParse():
    s = " foo (X ,a, b(c,Y)):- f(g(Y)), baz."
    strm = ParseStream(s)

    res = _parseRule(strm)
    print(res)

def testUnify1():
    s1= "f(l(a,l(b,l(c,nil))), R)."
    r1 = _parseRule(ParseStream(s1))

    s2= "f(l(H1, l(H2, Tl)), Tl)."
    r2 = _parseRule(ParseStream(s2))

    succ, bindings = _tryUnify(r1.head, r2.head)
    print(succ)
    print("\n".join(b[1] for b in bindings))

    print()
    print(r2)


def testUnify2():
    s1= "f(l(a,l(b,l(c,nil))), q)."
    r1 = _parseRule(ParseStream(s1))

    s2= "f(l(a, l(H2, Tl)), Tl)."
    r2 = _parseRule(ParseStream(s2))

    succ, bindings = _tryUnify(r1.head, r2.head)
    print(succ)
    print("\n".join(b[1] for b in bindings))

    print()
    print(r2)


def testUnifyUndo():
    s1= "f(X, q(Z), Z, Z)."
    r1 = _parseRule(ParseStream(s1))

    # S2 will fail, we'll retry with s3
    s2= "f(g(Y), Y, b, a)."
    r2 = _parseRule(ParseStream(s2))

    s3= "f(g(Y), Y, a, a)."
    r3 = _parseRule(ParseStream(s3))


    succ, bindings = _tryUnify(r1.head, r2.head)
    print(succ)
    print("\n".join(b[1] for b in bindings))

    print("undoing...")

    for b in reversed(bindings):
        b[0].unbind()

    print(r1)
    print(r2)
    print(r3)

    succ, bindings = _tryUnify(r1.head, r3.head)
    print(succ)
    print("\n".join(b[1] for b in bindings))


if __name__ == "__main__":
    print("Testing in clause.py")

    #testSimpleTerms()
    #testCopy()

    #testParse()

    testUnifyUndo()
