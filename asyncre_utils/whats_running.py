#!/usr/bin/env python
import os, sys
import re
import MySQLdb
from subprocess import check_output

# DB INFORMATION
sys.exit('EDIT DB INFO')
boinc_database_info = {'host': 'localhost', 'user': 'USERNAME',
                       'passwd': 'DBPASSWORD', 'db': 'DBNAME'}

def host_count(cpu_frac=0.75):
    db = MySQLdb.connect(**boinc_database_info)
    cursor = db.cursor()

    # For our purposes, this script looks through boinc userids 2 and 6 who have
    # host PC names that start with TECH, TCC, TLC, PH, LIB.
    # This is done primarily because there are several test clients with userids
    # 2/6 which we want to exclude.
    query = ('SELECT p_ncpus, id FROM host WHERE userid in (2,6) AND '
             'domain_name regexp "(TECH|TCC|TLC|PH|LIB)"')
    cursor.execute(query)

    total_cpus = 0
    for ncpus, hostid in cursor.fetchall():
        total_cpus += int(ncpus * cpu_frac)

    return total_cpus

def format_time(walltime, elapsed):
    if '-' in elapsed:
       d, t = elapsed.split('-')
    else:
       d, t = 0, elapsed
    d = int(d)
    items = map(int, t.split(':'))
    if len(items) == 1:
        s = items[0]
        h, m = 0, 0
    elif len(items) == 2:
        m, s = items
        h = 0
    else:
        h, m, s = items
    runtime = m + h*60 + d*60*24 + s/60.
    return 100 * runtime / float(walltime)

def main():
    default_dir = 'wcg'
    if len(sys.argv) == 2:
        default_dir = sys.argv[-1]
    base_dir = '~/projects/boincimpact'
    base_dir = os.path.join(base_dir, default_dir)
    print base_dir

    results = check_output('ps -eo "%p|%t|%a" | grep "AsyncRE_git"', shell=True)
    results = [r for r in results.split('\n') if r.endswith('.cntl')]

    total_cores = 0
    jobs = {}
    for r in results:
        items = r.split('|')
        pid, elapsed, cntl = items
	cntl = cntl.split()[-1]
        job_dir = cntl.split('.')[0]
        cntl_path = os.path.join(base_dir, job_dir, cntl)

        try:
            with open(cntl_path, 'r') as fin:
		contents = fin.read()

                match = re.search('TOTAL_CORES=(\d+)', contents)
                if not match: continue
	        cores = int(match.group(1))

                match = re.search('SUBJOB_CORES=(\d+)', contents)
                if not match: continue
                threads = int(match.group(1))
	        total_cores += cores * threads

		match = re.search('WALL_TIME=(\d+)', contents)
		if not match: continue
		wall_time = int(match.group(1))
                time_frac = format_time(wall_time, elapsed)
	        jobs[job_dir] = (cores*threads, time_frac, pid)

        except IOError: pass

    host_cpus = host_count()

    summary = "\n\tTotal jobs running on TU GRID:  {}/{} ({:.1%})\n"
    print summary.format(total_cores, host_cpus, float(total_cores)/host_cpus)

    # All for nice sorting of the jobnames
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_sort = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    nice_sort = lambda t: (int(t[-1][0]), alphanum_sort(t[0]))

    header = "\t{1[2]}\t{0:24}{1[0]:>9}\t{1[1]:>10}"
    fmt = "\t{1[2]}\t{0:24}{1[0]:>3} cores\t{1[1]:5.1f}"
    print header.format('Jobname', ('Cores', '% Complete', 'PID'))
    for kv in sorted(jobs.iteritems(), key=nice_sort):
        print fmt.format(*kv)

    print summary.format(total_cores, host_cpus, float(total_cores)/host_cpus)

if __name__ == "__main__":
    main()
