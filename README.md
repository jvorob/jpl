= JPL

J. Prolog Interpreter
(Any resemblance to other acronyms is purely coincidental)

Interpreter for a very simple dialect of prolog:
No integers, no cuts, no negation, no builtins

Written as an academic project


=== To Run

Run `python3 engine.py`
Gives interactive shell. User enters queries, system responds with answers. To get more answers for the same query, type ';' and enter.

Can load programs with `python3 engine.py $FILE`

I've included some test programs with the code. Try them out like so:

```
python3 engine.py test_progs/list.jpl
> list1(L), reverse(L, Rev).
> list1(L), subseq(L, Sub).

python3 engine.py test_progs/arithmetic.jpl
> showComposites(N, Div).
> peano=(+(5,3), 8).

```


=== Notes:

It's pretty slow for nontrivial programs (no indexing)
Watch out for infinite recursion
'\_' variables aren't special-cased, multiple underscore vars will share a binding


=== Cool things:

With the current design, it's almost possible to put variables into predicate or functor positions. e.g. something like `X(a).`, could return all unary predicates that are true of 'a'. Currently the parser doesn't handle this sort of case, but the execution loop is entirely capable of handling this, so it shouldn't be difficult to extend the language to support this.

Indexing is currently not used at all: each attempt to grab a clause loops through every single rule in the program. However, the clause-selection code is very modular, so it would be very straightforward to add in a simple implementation of indexing for a quick performance boost.
