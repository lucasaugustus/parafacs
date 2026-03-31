#! /usr/bin/env python3

from labmath3 import isprime, factorial, prod, mpz

with open("parafacs.txt", "r") as file:
    for (lineno, line) in enumerate(file, start=1):
        if line == "\n": continue
        l = line.split("  =  ")
        assert len(l) == 3, "Problem at line %d" % lineno
        formula, skeleton, factorstr = l
        
        print("\b"*42, formula, end='', flush=True)
        
        # First we validate and evaluate the formula.
        
        assert formula[ 0 ].isdecimal(), "Problem at line %d" % lineno
        assert formula[-1] != " ", "Problem at line %d" % lineno
        assert "!" in formula, "Problem at line %d" % lineno
        n, rest = formula.split("!")
        assert n.isdecimal(), "Problem at line %d" % lineno
        n = int(n)
        if rest == "": k = 0
        else:
            assert rest[:3] in (" + ", " - "), "Problem at line %d" % lineno
            sign = 1 if rest[:3] == " + " else -1
            rest = rest[3:]
            assert rest.isdecimal(), "Problem at line %d" % lineno
            k = sign * int(rest)
        
        N = factorial(n) + mpz(k)
        
        # The formula checks out, and we have our N.  Now we check the factors.
        assert factorstr[0].isdecimal(), "Problem at line %d" % lineno
        assert factorstr[-1] == "\n", "Problem at line %d" % lineno
        
        factorlist, factordict = [], {}
        for term in factorstr[:-1].split(" x "):
            if "^" in term:
                assert term.count("^") == 1, "Problem at line %d" % lineno
                term, exponent = term.split("^")
                assert exponent.isdecimal(), "Problem at line %d" % lineno
                exponent = int(exponent)
            else: exponent = 1
            assert term.isdecimal(), "Problem at line %d" % lineno
            term = int(term)
            factorlist.append(term)
            factordict[term] = exponent
        assert len(factorlist) == len(factordict), "Problem at line %d" % lineno
        assert prod(p**e for (p,e) in factordict.items()) == N, "Problem at line %d" % lineno
        assert factorlist == sorted(factorlist), "Problem at line %d" % lineno
        
        # The factors check out.  Now we examine the skeleton.
        assert skeleton[0] in ("PC"), "Problem at line %d" % lineno
        assert skeleton[-1].isdecimal(), "Problem at line %d" % lineno
        terms = skeleton.split(" x ")
        assert len(terms) == len(factordict), "Problem at line %d" % lineno
        for (term, (p,e)) in zip(terms, sorted(factordict.items())):
            assert " " not in term, "Problem at line %d" % lineno
            if "^" in term:
                assert term.count("^") == 1, "Problem at line %d" % lineno
                term, exponent = term.split("^")
                assert exponent.isdecimal(), "Problem at line %d" % lineno
                exponent = int(exponent)
            else: exponent = 1
            assert exponent == e, "Problem at line %d" % lineno
            if isprime(mpz(p)): assert term[0] == "P", "Problem at line %d" % lineno
            else:               assert term[0] == "C", "Problem at line %d" % lineno
            assert term[1:].isdecimal(), "Problem at line %d" % lineno
            assert int(term[1:]) == len(str(p)), "Problem at line %d" % lineno

print()

