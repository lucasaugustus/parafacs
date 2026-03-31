#! /usr/bin/env python3

import requests
from sys import argv
from subprocess import run
from time import time, sleep
from labmath3 import isprime, inf

# Default arguments
depth = 20
timeout = 8760      # hours
limit = inf
ecmonly = False

for arg in argv[1:]:
    arg = arg.split("=")
    if arg[0] == "depth"  : depth   =   int(arg[1])
    if arg[0] == "time"   : timeout = float(arg[1])
    if arg[0] == "num"    : limit   =   int(arg[1])
    if arg[0] == "ecmonly": ecmonly = True

timeout *= 3600     # timeout is now in seconds

def yafupretest(n):
    run("rm factor.log session.log factor.json nfs.dat.p nfs.dat.ranges nfs.fb nfs.job YAFU_get_poly_score.out", shell=True)
    #run("nice yafu3 'factor(%d)' -v -pretest %s -threads 28" % (n, depth), shell=True)  # 256.29
    run("nice yafu3 'factor(%d)' -v -pretest %s -threads 28 -prefer_gmpecm" % (n, depth), shell=True)   # 480.05
    #run("nice yafu3 'factor(%d)' -v -pretest %s -threads 28 -prefer_gmpecm_stg2" % (n, depth), shell=True)  # 629.02
    with open("factor.log", "r") as logfile:
        for line in logfile:
            line = line.partition(", ")[2]
            if line.startswith("div: found prime factor = "):
                x = int(line.split()[-1])
                n //= x
                yield x
            if line.startswith("prp"):
                x = int(line.split(" = ")[1].strip().split()[0])
                n //= x
                yield x
    run("rm factor.log session.log factor.json", shell=True)

def yafufactor(n):
    run("rm factor.log session.log factor.json nfs.dat.p nfs.dat.ranges nfs.fb nfs.job YAFU_get_poly_score.out", shell=True)
    run("nice yafu3 'factor(%d)' -v -threads 28 -plan light -xover 125" % (n), shell=True)
    with open("factor.log", "r") as logfile:
        for line in logfile:
            line = line.partition(", ")[2]
            if line.startswith("div: found prime factor = "):
                x = int(line.split()[-1])
                n //= x
                yield x
            if line.startswith("prp"):
                x = int(line.split(" = ")[1].strip().split()[0])
                n //= x
                yield x
    run("rm factor.log session.log siqs.dat factor.json", shell=True)

def cadofactor(n):
    run("rm cadoresult", shell=True)
    run("nice cado-nfs.py %d -t 28 | tee cadoresult" % n, shell=True)
    with open("cadoresult", "r") as cadoresult: factors = cadoresult.read().strip().split()
    run("rm cadoresult", shell=True)
    yield from map(int, factors)

def checkfdb(n):
    delay = 3
    try:
        for x in range(2):
            timeout = False
            try: response = requests.get('https://factordb.com/api', params={'query':str(n)}, timeout=delay)
            except requests.exceptions.Timeout: timeout = True
            if timeout: print("Request #%d timed out.  Trying again." % x)
            else:
                status = response.status_code
                if status == 200: break
                print("Got status code %d.  Trying again in %d seconds." % (status, delay))
                sleep(delay)
        else:
            print("Giving up on factordb.")
            return
        response = response.json()
        assert response["status"] != "P", (n, response)
        assert response["status"] != "PRP", (n, response)
        for (p,e) in response["factors"]:
            p = int(p)
            if isprime(p):
                yield p
    except KeyboardInterrupt: raise
    except:
        print(n)
        print(response)
        print(repr(response))
        raise

# This number and below have received t40+ work:
#with open("cleared", "r") as clearedfile: cleared = int(clearedfile.read().strip())

with open("composites", "r") as infile: composites = list(map(int, infile))
x, y, z = len(composites), 0, 1
limit = min(x, limit)

print("Pretesting", "all" if limit == inf else ("up to %d" % limit), "composites to a depth of %s.\n" % depth)
#print("Cleared up to %d.\n" % cleared)

# x: total number of composites
# y: index of the currently-conisdered composite in the list of composites, using 1 as the first index
# z: index of the currently-considered composite in the list of composites that actually got chugged on in this session,
#    using 1 as the first index, assuming that this composite has no new data found on factordb and therefore makes it to the
#    chugging stage
# limit: the maximum number of composites to chug on in this session

starttime = time()

try:
    for c in composites:
        y += 1
        #if c <= cleared: continue
        print("\n"*10)
        print(y, "/", limit)
        print(z)
        print(c)
        print(len(str(c)), "decimal digits")
        print(c.bit_length(), "bits")
        print(c.bit_length() // 64 + 1, "words")
        print()
        print("Checking factordb.com...")
        fdb_results = list(checkfdb(c))
        if fdb_results:
            print("Found factors on factordb.com:")
            print(fdb_results)
            with open("results", "a") as outfile:
                for p in fdb_results:
                    outfile.write(str(p) + "\n")
            continue
        print("Found nothing.")
        
        cc = c
        preprimes = list(yafupretest(cc))
        for p in preprimes:
            assert isprime(p), (c, p)
            assert c % p == 0, (c, p)
            with open("results", "a") as outfile: outfile.write(str(p) + "\n")
            cc //= p
        postprimes = []
        if (not ecmonly) and (1 < cc < 10**150):
            postprimes = list(yafufactor(cc) if cc < 10**110 else cadofactor(cc))
            for p in postprimes:
                assert isprime(p), (cc, p)
                assert cc % p == 0, (cc, p)
                with open("results", "a") as outfile: outfile.write(str(p) + "\n")
        primes = preprimes + postprimes
        if primes:
            with open("results_for_factordb", "a") as outfile: outfile.write(str(c)+" = "+" * ".join(map(str, primes))+"\n")
        #with open("cleared", "w") as clearedfile: clearedfile.write(str(c))
        if z >= limit: break
        z += 1
        
        with open("results", "r") as results: resultsnum = len(results.readlines())
        with open("results_for_factordb", "r") as results: fdblines = len(results.readlines())
        print("\n"*3)
        print("The results file now contains %d numbers." % resultsnum)
        print("There are %d lines in the fdb upload file." % fdblines)
        print("\n"*3)
        newtime = time()
        if newtime - starttime > timeout: break
        
        # Composites remaining: limit - y
        # Composites chugged on in this session: z - 1
        
        print("There are", limit - y, "composites remaining.")
        print("The wall-clock time taken so far this session is %0.2f hours." % ((newtime - starttime) / 3600))
        ettc = (newtime - starttime) * (limit-y) / (z-1)
        print("The ettc is %d seconds, or %.2f hours." % (ettc, ettc / 3600))
        
        sleep(1)

except KeyboardInterrupt: pass

print("\n" * 5)

import assimilate

#while true; do while [ $(date +%H:%M) != "00:00" ]; do sleep 30; done; time ./factorcomposites.py depth=45 time=3; done

