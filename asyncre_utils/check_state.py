#!/usr/bin/env python
import os
import re
import sys
import glob

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def main(dirname):
    replicas = {}
    for filename in glob.glob(dirname + '/r*/*'):
        _, replica, fname = filename.split(os.sep)
        if fname == dirname + ".out": continue
        replica = int(replica[1:])
	if not replicas.get(replica, 0):
            replicas[replica] = {'inp': 0, 'out': 0}
        if fname.endswith('.inp'):
            cycle = int(fname.split('_')[-1].split('.')[0])
            if cycle > replicas[replica]['inp']: replicas[replica]['inp'] = cycle
        elif fname.endswith('.out'):
            cycle = int(fname.split('_')[-1].split('.')[0])
            if cycle > replicas[replica]['out']: replicas[replica]['out'] = cycle

    print dirname
    bad = []
    for r, d in replicas.iteritems():
        i, o = d['inp'], d['out']
        if i != o + 1 and i != o:
	    bad.append((r, i, o))
            print "{}:  .inp: {}   .out: {}".format(r, i, o)

    statfile = os.path.join(dirname, dirname + '_stat.txt')
    with open(statfile, 'r') as fin:
	lines = fin.readlines()

    for k, line in enumerate(lines):
	for r, i, o in bad:
	    if line.lstrip().startswith(str(r)):
	        lines[k] = rreplace(line, str(i), str(o+1), 1)


    with open(statfile, 'w') as fout:
        fout.writelines(lines)

if __name__ == "__main__":
    dirname = sys.argv[1]
    if not os.path.exists(dirname):
        print "{} doesn't exist!".format(dirname)
        sys.exit(1)
    main(dirname)
