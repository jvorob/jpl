# //python 3


"""
NOTES/TODO list:



A Term is a variable or an atom, possibly with children
QUESTION: Do we special-case atoms or just have them be functor/0?

Variables are a string key and a context (either the parent rule or a CTX object)

A clause is just a term,

A rule is a head clause, followed by a list of body clauses
+ a context (which stores variables defined in that rule's clauses)
QUESTION: do clauses carry a ptr to the rule/context?
ANSWER: I think no, it's stored in the var, only needs to be updated on rule copy


- Rule methods: copy (copies context)

- Variable methods:  
    - BindTo(term)
    - Unbind
    - Deref: (returns a term, if bound, or var, if unbound)

- Term methods?: Unify(term) #updates bindings, returns T or F, returns list of bindings made?
    - isVar?





QUESTION: how to create rules/terms?
- Term AST: tree of functor/var tokens
- Rule AST: head termAST, list of body termAST

"""


class Term:
    """ Represents a var or functor (or atom if functor/0) 
Vars should be bound to a rule instance (that's the binding context)
    """

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
    def __init__(self, token, context):
        " token is var name, context is Rule object "
        super().__init__()
        self.token = token
        assert isinstance(context, Rule)
        self.context = context

    def deref(self):
        " Recursively dereferences self until reach nonvar or unbound var "
        " If unbound, returned value is var"

        if self.token not in self.context.bindings:
            return self #returns the deepest unbound var

        # we're bound, deref once
        binding = self.context.bindings[self.token]

        #TODO: put isVar into Term class

        if not isinstance(binding, Var):
            # If hit nonvar, we're done
            return binding
        else:
            # If hit var, continue
            assert binding != self #this shouldn't happen, also we shouldn't get loops
            # NOTE: must always bind deepest var in chain only for this to be true

            return binding.deref()



    def bindTo(self, term):
        " Binds self <= term, returns the var instance which got changed "
        # NOTE: binding is set on deepest var in chain
        # Ensures non-loops (I think), and ensures undoing preserves older structure

        # Get deepest bound var
        # NOTE: if deepvar is a Functor, then that means self was already bound
        deepvar = self.deref() 
        assert isinstance(deepvar, Var), "Can't re-bind an already-bound var"

        # make binding & return the var that was updated
        deepvar.context.bindings[deepvar.token] = term
        return deepvar 



    def __repr__(self):
        return self.safeStr()

    def safeStr(self, depth=10):
        if depth == 0:
            return "..."

        boundval = self.deref()
        if isinstance(boundval, Var):
            return "(${}={})".format(self.token, boundval.token)
        else:
            # we have a functor
            return "(${}={})".format(self.token,boundval.safeStr(depth-1))


class Rule:
    " Represents an instance of a rule (e.g. multiple invocations make multiple rule objs) "

    def __init__(self):
        self.bindings = {}
        pass

    def __repr__(self):
        return "<Rule, Vars:{}>".format(self.bindings)


if __name__ == "__main__":
    print("Hi")

    r = Rule()
    print(r)


    f1 = Functor("a",[])

    v1 = Var("X", r)
    v2 = Var("Y", r)
    v3 = Var("Y", r)

    f2 = Functor("foo",[f1,v1,v2,v3])

    v1.bindTo(f1)
    v3.bindTo(v1)
    print(f2)
