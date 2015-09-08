#!/usr/bin/env python
import os
import re
import sys

def main(dirname, N_cores):
    if dirname.endswith(os.sep):
        dirname = dirname[:-1]

    cntl_path = os.path.join(dirname, dirname + ".cntl")
    with open(cntl_path, 'r') as fin:
        lines = fin.readlines()

    for i, line in enumerate(lines):
        match = re.search(r'TOTAL_CORES=[0-9]+', line)
        if match:
            lines[i] = re.sub(r'[0-9]+', N_cores, line)

    with open(cntl_path, 'w') as fout:
        fout.writelines(lines)

    print "%s updated to read TOTAL_CORES=%s"%(cntl_path, N_cores)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Please specify a directory and new number of cores"
        sys.exit(2)
    dirname = sys.argv[1]
    if not os.path.exists(dirname):
        print "Directory specified does not exist"
        sys.exit(2)
    N_cores = sys.argv[2]
    try:
        float(N_cores)
    except Exception as e:
        print "Please specify an appropriate number of cores"
        sys.exit(2)
    main(dirname, N_cores)
