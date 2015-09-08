#!/usr/bin/env python
"""
This script will attempt to measure the average time AsyncRE BOINC jobs spend
in each of the 3 states:
    1. Waiting/exchanging
    2. Running MD
    3. Transport or I/O bound overhead

Waiting/exchanging time should be the time between jobname_rN_cM.out was created
and jobname_rN_c(M+1).inp was last modified.  This can be measured from the
filesystem using os.stat on the appropriate files.

Computing time for jobname_rN_cM can be extracted directly from the appropriate
result entry in the boincimpact database. Extracting the exact start/end time of
the computing will be inexact because it will need to be parsed from the
stderr.txt text.

Overhead can be computed in several places:
    - Time between jobname_rN_cM.inp is last modified to the sent time of the
      workunit corresponding to that cycle.
    - Time between sent time of the workunit and the best estimate of the start
      time of the executable.
    - Time between end time of the executable and the received time of the
      corresponding workunit.
    - Time between the received time and the writing of jobname_rN_cM.out

This script will operate on one job directory, namely it will take a single
command line argument $BOINC/wcg/jobname/.
"""
import os
import re
import sys
import shutil
import MySQLdb
import datetime
from dateutil import tz

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

UTC = tz.gettz('UTC')
LOCAL = tz.gettz('America/New_York')

# DB INFORMATION
sys.exit('EDIT DB INFO')
boinc_database_info = {'host': 'localhost', 'user': 'USERNAME',
                       'passwd': 'DBPASSWORD', 'db': 'DBNAME'}

def convert_local_timestamp(t):
    # returns datetime with NYC timezone
    return datetime.datetime.fromtimestamp(t).replace(tzinfo=LOCAL)

def convert_utc_timestamp(t):
    return datetime.datetime.utcfromtimestamp(t).replace(tzinfo=UTC).astimezone(LOCAL)

def ostime_to_dt(f):
    return convert_local_timestamp(os.stat(f).st_mtime)

def get_filesystem_info(jobdir, jobname):
    data = {}
    base_string = os.path.expanduser('~/projects/boincimpact/wcg/')
    base_string += os.path.join('{jn}', 'r{rn}', '{jn}_{cn}.{ext}')
    for root, _, files in os.walk(jobdir):
        match = re.search(r'.*r(\d+)', root)
        if not match: continue
        rnum = int(match.group(1))
        for cnum in xrange(1, 10000):
            ind = 'r%i_c%i'%(rnum, cnum)
            prev_rst = base_string.format(jn=jobname, rn=rnum, cn=cnum-1, ext='rst')
            curr_inp = base_string.format(jn=jobname, rn=rnum, cn=cnum, ext='inp')
            curr_rst = base_string.format(jn=jobname, rn=rnum, cn=cnum, ext='rst')

            # only process fully completed cycles
            if not all(map(os.path.exists, (prev_rst, curr_inp, curr_rst))):
                break
            data[ind] = {}

            prev_rst_time = os.stat(prev_rst).st_mtime
            curr_inp_time = os.stat(curr_inp).st_mtime
            curr_rst_time = os.stat(curr_inp).st_mtime

            data[ind]['prev_rst'] = ostime_to_dt(prev_rst)
            data[ind]['curr_inp'] = ostime_to_dt(curr_inp)
            data[ind]['curr_rst'] = ostime_to_dt(curr_rst)

    return data

def get_database_info(jobname, fsdata):
    db = MySQLdb.connect(**boinc_database_info)
    cursor = db.cursor()

    regexp = "{}_r%%_c%%".format(jobname)
    query = ("SELECT workunit.name, result.sent_time, result.received_time, "
             "result.cpu_time, result.stderr_out FROM result INNER JOIN "
             "workunit ON result.workunitid=workunit.id WHERE result.userid=2 "
             "AND result.outcome=1 AND workunit.name LIKE '{}'".format(regexp))

    cursor.execute(query)

    utc = tz.gettz('UTC')
    local = tz.gettz('America/New_York')

    repeat_flag = 'r0_c0'

    for wu_name, sent_time, rcvd_time, cpu_time, std_out in cursor.fetchall():
        rnum, cnum = map(int, re.search(r'.*r(\d+)_c(\d+)', wu_name).group(1, 2))
        ind = 'r%i_c%i'%(rnum, cnum)

        # Avoid sql records which don't have file timestamps from previous func.
        # This is needed because for systems which have run for a while, there
        # are many cycles and the os.walk in the previous function can take some
        # time.  In that time, new results can be added to the sql database but
        # the files associated with these results weren't present for the
        # previous function to get timestamps.
        if ind not in fsdata:
            continue

        # Needed to remove outliers caused by cycles repeating. No replica
        # should have more than 1 successful result for each cycle.
        if ind == repeat_flag:
            del fsdata[ind]
            continue
        repeat_flag = ind

        sent_time = convert_utc_timestamp(sent_time)
        rcvd_time = convert_utc_timestamp(rcvd_time)

        st_time = re.search('(\d\d):(\d\d):(\d\d).*wrapper.*starting', std_out)
        if not st_time: continue
        st_time = map(int, st_time.group(1, 2, 3))

        en_time = re.search('(\d\d):(\d\d):(\d\d).*impact exited', std_out)
        if not en_time: continue
        en_time = map(int, en_time.group(1, 2, 3))

        mintime = datetime.datetime.min.time()
        midnight = datetime.datetime.combine(rcvd_time.date(), mintime)
        midnight = midnight.replace(tzinfo=local)

        st_time = midnight + datetime.timedelta(hours=st_time[0],
                                                minutes=st_time[1],
                                                seconds=st_time[2])
        en_time = midnight + datetime.timedelta(hours=en_time[0],
                                                minutes=en_time[1],
                                                seconds=en_time[2])
        if st_time > en_time:
            st_time -= datetime.timedelta(days=1)
        if en_time > rcvd_time and en_time.date() == rcvd_time.date():
            st_time -= datetime.timedelta(days=1)
            en_time -= datetime.timedelta(days=1)

        assert sent_time < st_time < en_time < rcvd_time, (sent_time, st_time,
                en_time, rcvd_time)

        fsdata[ind]['cpu_time'] = cpu_time
        fsdata[ind]['sent_time'] = sent_time
        fsdata[ind]['rcvd_time'] = rcvd_time
        fsdata[ind]['st_time'] = st_time
        fsdata[ind]['en_time'] = en_time

    return fsdata

def quick_stats(df, jobname):
    qfix = lambda x: pd.Timedelta(np.timedelta64(np.timedelta64(x, 'ns'), 's'))
    stats = lambda s: (s.median(), map(qfix, s.quantile([0.25, 0.75]).values))

    MD, MDstd = stats(df.MD_time)
    ex, exstd = stats(df.exchange_time)
    boinc, boincstd = stats(df.boinc_overhead)
    fs, fsstd = stats(df.fs_overhead)
    overhead, overheadstd = stats(df.total_overhead)
    total, totalstd = stats(df.total_overhead + df.MD_time + df.exchange_time)
    frac = overhead / (total)

    print "\n\tStats for job:  {}".format(jobname)
    print "\n\tMedian MD Time:\n\t\t{0}  ({1[0]}, {1[1]})".format(MD, MDstd)
    print "\n\tMedian Exchange Time:\n\t\t{0} ({1[0]}, {1[1]})".format(ex, exstd)
    print "\n\tMedian Boinc Overhead:\n\t\t{0} ({1[0]}, {1[1]})".format(boinc, boincstd)
    print "\n\tMedian Filesystem Overhead:\n\t\t{0} ({1[0]}, {1[1]})".format(fs, fsstd)
    print "\n\tMedian Total Overhead:\n\t\t{0} ({1[0]}, {1[1]})".format(overhead, overheadstd)
    print "\n\tMedian Total Cycle Time:\n\t\t{0} ({1[0]}, {1[1]})".format(total, totalstd)
    print "\n\tTime Wasted Fraction:\n\t\t{}\n".format(frac)

def distribution_plot(df, jobname, resolution='minutes'):
    def boxplot(series, maxcutoff, jobname, filename, resolution):
        convert_to_hours = lambda ntd: ntd / np.timedelta64(1, 'h')
        convert_to_minutes = lambda ntd: ntd / np.timedelta64(1, 'm')

        func = convert_to_hours if resolution == 'hours' else convert_to_minutes
        series = series.apply(func)

        color = dict(boxes='black', medians='red', whiskers='gray', caps='gray')
        meanprops = dict(linestyle='--', linewidth=1, color='blue')

        params = dict(vert=False, notch=False, widths=0.8, color=color,
                      sym='r.', whis=[5, 95], showmeans=True,
                      meanprops=meanprops, showfliers=True, meanline=True)

        series.plot(kind='box', **params)

        q = func(maxcutoff)
        plt.xlim(0, q)

        plt.xlabel(resolution)
        plt.title(jobname)

        # toggle off y grid
        plt.grid(axis='y', which='both')
        plt.tight_layout()
        plt.savefig(filename)

    df['total_time'] = df.MD_time + df.exchange_time + df.total_overhead
    series = df[['MD_time', 'exchange_time', 'total_overhead', 'total_time']]
    cutoff = df.total_time.quantile(0.99)

    boxplot(series, cutoff, jobname, jobname+'_boxplot.png', resolution)

    series = df[['boinc_overhead', 'fs_overhead', 'total_overhead']]
    cutoff = df.total_overhead.quantile(0.99)

    boxplot(series, cutoff, jobname+' overhead',
            jobname+'_overhead_boxplot.png', resolution)

def winsorize(s, qs=[0.01, 0.99]):
    # In constrast to truncating the extreme values in a distribution,
    # winsorization sets the extreme values equal to a percentile cutoff. Here
    # the default is the 1st and 99th percentile.  This allows us to "include"
    # the extreme outliers (which shouldn't be due to boinc errors) in plotting
    # without having huge ranges in x/y.
    q1, q2 = s.quantile(qs)
    q1 = np.timedelta64(np.timedelta64(q1.value, 'ns'), 's')
    q2 = np.timedelta64(np.timedelta64(q2.value, 'ns'), 's')
    s[s < q1] = q1
    s[s > q2] = q2
    return s

def build_profiles(jobdir):
    if jobdir.endswith(os.sep):
        jobdir = jobdir[:-1]
    jobname = jobdir.split(os.sep)[-1]

    fsdata = get_filesystem_info(jobdir, jobname)

    all_data = get_database_info(jobname, fsdata)

    # build table of all data
    df = pd.DataFrame.from_dict(all_data).T

    df['MD_time'] = df.en_time - df.st_time
    df['exchange_time'] = df.curr_inp - df.prev_rst

    df['boinc_overhead'] = df.rcvd_time - df.en_time
    df['boinc_overhead'] += df.st_time - df.sent_time

    df['fs_overhead'] = df.sent_time - df.curr_inp
    df['fs_overhead'] += df.curr_rst - df.rcvd_time

    # remove EXTREME outliers via winsorization
    series = ['MD_time', 'exchange_time', 'fs_overhead', 'boinc_overhead']
    df[series] = df[series].apply(winsorize, axis=1)

    df['total_overhead'] = df.boinc_overhead + df.fs_overhead
    df.to_csv(jobname + '.csv')

    quick_stats(df, jobname)
    distribution_plot(df, jobname)

def main():
    usage = "\nUsage:\n\t {0} jobdir\n".format(sys.argv[0])
    if len(sys.argv) != 2:
        print usage
        sys.exit(1)

    jobdir = sys.argv[1]
    if not os.path.exists(jobdir):
        print "\tError: {0} doesn't exist".format(jobdir)
        sys.exit(1)

    build_profiles(jobdir)

if __name__ == "__main__":
    main()
