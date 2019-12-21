# //python 3


"""
NOTES/TODO list:

TODO:
- AST: basic def
- AST: make rule from AST
- Term: Unify (returns bindings)
- Term: undo bindings


TODO-EVENTUAL:
- Parse text to AST
- List pretty-print
- List parse
- less-verbose printer (add verbose flag to terms)
- Goal list / eval step (+pretty print)
- Outer interp
- Pre-unify


A Term is a variable or an atom, possibly with children

Variables are a string key and a context (either the parent rule or a CTX object)

A clause is just a term


A rule is a head clause, followed by a list of body clauses
+ a context (which stores variables defined in that rule's clauses)



QUESTION: how to create rules/terms?
- Term AST: tree of functor/var tokens
- Rule AST: head termAST, list of body termAST


NOTE: Creation conventions:

- Variables are created WITHOUT A CONTEXT
- HOWEVER: if a variable is derefed or bound without a context, we raise an exception
- Rules must be created with terms already made,
- Rule initializer binds all vars in tree

"""


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
            mapfun(child)


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



if __name__ == "__main__":
    print("Hi")

    #testSimpleTerms()
    testCopy()
