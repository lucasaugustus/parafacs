#! /usr/bin/env python3

from labmath3 import isprime, prod, mpz
from shutil import copyfile, move
from itertools import chain
from time import sleep
import requests

# Part 1: Integrate results into parafacs.txt.

print("Integrating results into parafacs.txt...")
print()

def resultstr(n, i, f):
    outstr = str(n) + "!" + ((" %s %d" % ('+' if i > 0 else '-', abs(i))) if i != 0 else '') + "  =  "
    for p in sorted(f):
        multiplicity = '' if f[p] == 1 else ("^%d" % f[p])
        outstr += ('P' if isprime(mpz(p)) else 'C') + str(len(str(p))) + multiplicity + " x "
    outstr = outstr[:-2] + " =  "
    for p in sorted(f):
        multiplicity = '' if f[p] == 1 else ("^%d" % f[p])
        outstr += str(p) + multiplicity + " x "
    outstr = outstr[:-3]
    return outstr

with open("results", "r") as infile: newprimes = list(map(int, chain(*(line.split() for line in infile))))
for p in newprimes: assert isprime(mpz(p)), p

with open("parafacs.txt", "r") as infile, open("parafacs.txt.new", "w") as outfile, open("history.txt", "a") as historyfile:
    for line in infile:
        if "C" not in line:
            outfile.write(line)
            continue
        lineparts = line.split('=')
        # We are working on "n! + k", "n!", or "n! - k", for some n and k.
        head = lineparts[0].strip()
        if '+' in head:
            n, k = head.split('+')
            assert n[-2:] == "! "
            n = int(n[:-2])
            assert k.strip().isnumeric()
            k = int(k)
        elif '-' in head:
            n, k = head.split('-')
            assert n[-2:] == "! "
            n = int(n[:-2])
            assert k.strip().isnumeric()
            k = - int(k)
        else:
            assert head[-1] == '!'
            n, k = int(head[:-1]), 0
        # Now we have n and k.
        
        N = prod(range(1, n+1)) + k
        
        # Now we process the known factors.
        assert len(lineparts) == 3
        tail = lineparts[2].strip().split(" x ")
        flist = []
        # We will assume that no composite cofactor is raised to a power greater than 1.
        for term in tail:
            if '^' not in term: term += "^1"
            p, e = map(int, term.split('^'))
            assert N % (p**e) == 0, (N, n, k, p, e)
            if isprime(mpz(p)): flist.extend([p] * e)
            else:
                for pp in newprimes:
                    while p % pp == 0:
                        flist.append(pp)
                        p //= pp
                    if p == 1: break
                if p != 1: flist.append(p)
        assert prod(flist) == N, (n, k, flist, line)
        f = {}
        for p in flist: f[p] = f.get(p, 0) + 1
        assert prod(p**e for (p,e) in f.items()) == N
        
        newstr = resultstr(n, k, f)
        orig = line.strip()
        if orig != newstr:
            print(orig)
            print(newstr)
            historyfile.write(newstr + '\n')
            print()
        outfile.write(newstr + '\n')

copyfile("parafacs.txt", "parafacs.txt.bkp")
move("parafacs.txt.new", "parafacs.txt")

# Part 2: Extract composites from parafacs.txt.

print("Extracting composites...")

composites = set()

with open("parafacs.txt", "r") as infile:
    for line in infile:
        if "C" not in line: continue
        
        lineparts = line.split('=')
        assert len(lineparts) == 3
        tail = lineparts[2].strip().split(" x ")
        
        for term in tail:
            if '^' in term: term = term.split('^')[0]
            term = int(term)
            if isprime(mpz(term)): continue
            composites.add(term)

sortedcomposites = sorted(composites)
print()
print("Found", len(composites), "composites.")
for x in (0, -1):
    y = sortedcomposites[x]
    print(("Min","Max")[x]+"imum:", len(str(y)), "decimal digits /", y.bit_length(), "bits /", y.bit_length()//64 + 1, "words.")

with open("composites", "w") as outfile:
    for x in sorted(composites):
        outfile.write(str(x) + '\n')

print()

# Part 3: Upload results_for_factordb.

print("Reporting factors...")
print()

with open("results_for_factordb", "r") as results: result = results.read().strip()
resultcount = len(result.splitlines())

print(result)

reply = requests.post("http://factordb.com/report.php", data={"report": result, "format": 0}).text

print()
print("Results reported:         %d" % resultcount)
print("New factors added:        %d" % reply.count("Factor added"))
print("Factors already known:    %d" % reply.count("Factor already known"))
print("Small factors:            %d" % reply.count("Small factor"))
print("Errors (does not divide): %d" % reply.count("Does not divide"))
print()
print("Checking uploads...")
print()

def checkfdb(n):
    delay = 3
    try:
        while True:
            response = requests.get('https://factordb.com/api', params={'query':str(n)})
            status = response.status_code
            if status == 200: break
            print("Got status code %d.  Trying again in %d seconds." % (status, delay))
            sleep(delay)
        response = response.json()
        assert response["status"] != "P", (n, response)
        assert response["status"] != "PRP", (n, response)
        for (p,e) in response["factors"]:
            p = int(p)
            if isprime(mpz(p)):
                yield p
    except KeyboardInterrupt: raise
    except:
        print(n)
        print(response)
        print(repr(response))
        raise

successes, failures = 0, 0
for line in result.splitlines():
    print(line, end=' ', flush=True)
    n, fac = line.split(" = ")
    n, fac = int(n), [int(x.split("^")[0]) for x in fac.split(" * ")]
    yafudata = list(checkfdb(n))
    if all(x in yafudata for x in fac):
        successes += 1
        print("passed.")
    else:
        failures += 1
        print("failed.")
else:
    if successes == resultcount and failures == 0:
        print()
        print("All results successfully uploaded.")
        print()
        print("Blanking result files...")
        with open("results_for_factordb", "w") as _: pass
        with open("results", "w") as _: pass
        print()
        print("Done.")
    else:
        print("There was a problem with at least one upload.")
    exit()




