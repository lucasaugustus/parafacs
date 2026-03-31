#! /usr/bin/env python3

from labmath3 import factorial, isprime

for f in range(104, 151):
    fac = factorial(f)
    l = len(str(fac))
    for n in range(f-1, 0, -1): print("%d! - %d  =  %s%d  =  %d" % (f, n, 'P' if isprime(fac - n) else 'C', l, fac - n))
    print("%d!  =  C%d  =  %d" % (f, l, fac))
    for n in range( 1 , f,  1): print("%d! + %d  =  %s%d  =  %d" % (f, n, 'P' if isprime(fac + n) else 'C', l, fac + n))


"""
"""

