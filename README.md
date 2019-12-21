## JPL

J. Prolog Interpreter
(Any resemblance to other acronyms is purely coincidental)

Interpreter for a very simple dialect of prolog:
No integers, no cuts, no negation, no builtins (except `_` handling)

Written as an academic project. Inspired by the paper _'A Hitchiker's Guide to Reinventing a Prolog Machine'_, by Paul Tarau, ICLP2017


### To Run

Running `python3 jpl.py` gives an interactive shell for a demo prolog program. The user enters queries, the system responds with answers. To get more answers for the same query, type ';' and enter.

Can load other prolog sources with `python3 jpl.py $FILE`

I've included some test programs with the code. Try them out like so:

```
python3 jpl.py test_progs/list.jpl
> list1(L), reverse(L, R).
    L = l(1, l(2, l(3, nil)))
    R = l(3, l(2, l(1, nil)))

    yes

> list1(L), subseq(L, Sub).
    L = l(1, l(2, l(3, nil)))
    Sub = l(1, l(2, l(3, nil)));

    L = l(1, l(2, l(3, nil)))
    Sub = l(1, l(2, nil))

    yes

python3 jpl.py test_progs/arithmetic.jpl
> showComposites(N, Div).
    % ...
> peano=(+(5,3), 8).
    % ...
```


### Notes:

It's pretty slow for nontrivial programs (no indexing)
Watch out for infinite recursion


### Cool things:

With the current design, it's almost possible to put variables into predicate or functor positions. e.g. something like `X(a).`, could return all unary predicates that are true of 'a'. Currently the parser doesn't handle this sort of case, but the execution loop is entirely capable of handling this, so it shouldn't be difficult to extend the language to support this.

Indexing is currently not used at all: each attempt to grab a clause loops through every single rule in the program. However, the clause-selection code is very modular, so it would be very straightforward to add in a simple implementation of indexing for a quick performance boost.
