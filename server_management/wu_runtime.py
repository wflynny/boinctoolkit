#!/usr/bin/env python
import re
import datetime
import MySQLdb
from dateutil import tz

class Result(object):
    def __init__(self, hostname, ncpus, cpu_time, received_time, stderr_out):
        self.hostname = hostname
        self.N_cpus = ncpus
        self.cpu_time = cpu_time
        self.received_time = received_time
        self.stderr_out = stderr_out

        self._parse_times()

    def convert_utc_to_local(self, d):
        utctz = tz.gettz('UTC')
        local = tz.gettz('America/New_York')
        d = d.replace(tzinfo=utctz)
        return d.astimezone(local)

    def _parse_times(self):
        """
        TODO: Change this so that it can pick up when the jobs stalled, if
        that happened at all."""

        cpu_time = self.cpu_time

        re_str = r'([0-9]{2}:[0-9]{2}:[0-9]{2}).*wrapper:\srunning'
        first_start_time = re.findall(re_str, self.stderr_out)[0]
        first_start_time_items = map(int, first_start_time.split(':'))
        re_str = r'([0-9]{2}:[0-9]{2}:[0-9]{2}).*called\sboinc_finish'
        end_time = re.findall(re_str, self.stderr_out)[0]
        end_time_items = map(int, end_time.split(':'))

        # All of this is to massage the start/end times into datetime format
        duration_h = int(cpu_time/3600)
        duration_m = int(cpu_time%3600/60)
        duration_s = cpu_time%60

        received_dt = datetime.datetime.utcfromtimestamp(self.received_time)
        received_dt = self.convert_utc_to_local(received_dt)

        dayflip = 1 if end_time_items[0] >= 20 and received_dt.hour < 20 else 0
        endtime_dt = datetime.datetime(received_dt.year, received_dt.month,
                                       received_dt.day-dayflip, *end_time_items)
        starttime_dt = endtime_dt - datetime.timedelta(hours=duration_h,
                                                       minutes=duration_m,
                                                       seconds=duration_s)
        first_start_time = starttime_dt.replace(hour=first_start_time_items[0],
                                                minute=first_start_time_items[1],
                                                second=first_start_time_items[2])

        self.start_time = starttime_dt
        self.first_start_time = first_start_time
        self.end_time = endtime_dt

def get_results(outcome, userid, app_version_str='>=0'):
    """
    Returns all results for a particular userid with a specified outcome.
    Further refine with app_version_id =,<,>,<=,>="""

    app_ver_str = 'app_version_id%s'%app_version_str

    # EDIT DB_INFO THEN REMOVE sys.exit
    sys.exit('EDIT DB INFO')
    boinc_database_info = {'host': 'localhost', 'user': 'USERNAME',
                           'passwd': 'DBPASSWORD', 'db': 'DBNAME'}
    db = MySQLdb.connect(**boinc_database_info)

    cursor = db.cursor()
    cursor.execute("SELECT host.domain_name, host.p_ncpus, result.cpu_time, "
                   "result.received_time, result.stderr_out FROM host INNER "
                   "JOIN result ON host.id=result.hostid WHERE result.userid=2"
                   " AND outcome=1 AND %s"%app_ver_str)

    return cursor.fetchall()

def dtfloor(dt):
    return dt - datetime.timedelta(minutes=dt.minute%5, seconds=dt.second,
                                   microseconds=dt.microsecond)

def dt2num(dt):
    s = str(dt.date().toordinal())
    return float(s + ''.join(dt.time().isoformat().split(':')))

