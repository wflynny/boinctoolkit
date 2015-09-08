#!/usr/bin/env python
import os
import sys
import subprocess

def main(pattern):
    try:
        cmd = 'ps -eo "%p|%t|%a" | grep -v "grep" | grep "{}"'.format(pattern)
        results = subprocess.check_output(cmd, shell=True)
        results = [r for r in results.split('\n') if r.endswith('.cntl')]
        results = [r.split('|')[::2] for r in results]
    except Exception as e:
        print e
        print "\n\tNo results found matching pattern:  {0}\n".format(pattern)
        print "\tPlease try again.\n"
        sys.exit(1)


    if len(results) == 0:
        print "\n\tNo results found matching pattern:  {0}\n".format(pattern)
        print "\tPlease try again.\n"
        sys.exit(0)

    print "\n\tFound the following running jobs "
    print "\tthat match pattern:  {0}\n".format(pattern)


    for pid, jobname in results:
        print "\t{0}:  {1}".format(pid, jobname.split()[-1])

    confirm = raw_input("\n\tKill these jobs? [y/N]")
    if not confirm.lower().startswith('y'):
        print "\tAborting...\n"
        sys.exit(0)

    for pid, _ in results:
        subprocess.call("kill %s"%pid, shell=True)
    print "\n\tJobs killed. Good-bye.\n"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "\tPlease specify a jobname pattern to match"
        sys.exit(2)

    main(sys.argv[1])
