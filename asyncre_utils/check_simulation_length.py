#!/usr/bin/env python
import os
import sys
import re
import argparse

def main():
    des = "Returns highest cycle number from *_#.out files in specified dir"
    parser = argparse.ArgumentParser(description=des)
    parser.add_argument('directory', help="system directory to search")
    args = parser.parse_args()

    directory = args.directory
    if directory.endswith('/'): directory = directory[:-1]

    replicas = {}
    for root, dirs, files in os.walk(directory):
        replica = re.search(r'.*r(\d+)', root)
        if not replica: continue
        replica = replica.group(1)
        max_cycle = 0
        for f in files:
            if f.endswith('.out'):
                try:
                    n = re.search(r'_(\d+).out', f)
		    if not n: continue
                    n = int(n.group(1))
                    if n > max_cycle:
                        max_cycle = n
                except Exception as e:
                    print e
                    pass
        replicas[replica] = max_cycle

    if len(replicas) == 0:
        print "\n\tCannot find that directory...\n"
        sys.exit(0)

    sorted_replicas = [t[::-1] for t in sorted(replicas.iteritems(),
                                               key=lambda t: t[-1])]
    min_cycle, min_replica = sorted_replicas[0]
    max_cycle, max_replica = sorted_replicas[-1]
    avg = sum(r[0] for r in sorted_replicas)
    avg /= len(sorted_replicas)

    print
    print "\tLowest completed cycle for system    {0}  :  cycle {1} (r{2})".format(directory, min_cycle, min_replica)
    print "\tHighest completed cycle for system   {0}  :  cycle {1} (r{2})".format(directory, max_cycle, max_replica)
    print "\tAverage number of cycles for system  {0}  :  {1} cycles".format(directory, avg)
    print


if __name__ == "__main__":
    main()
