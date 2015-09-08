#!/usr/bin/env python
import re
import os
import sys
import time
import signal
import MySQLdb
import smtplib
import logging
import argparse
from operator import itemgetter

import datetime
from dateutil import tz

EPOCH = datetime.datetime(1970, 1, 1, tzinfo=tz.gettz('UTC'))

class HostWatcher(object):
    def __init__(self, cycle_time, userids=None, last_time=0, plotter=False):
        self.cycle_time = cycle_time

        self.userids = userids

        self.last_time = last_time

        # EDIT DB_INFO THEN REMOVE sys.exit
        sys.exit('EDIT DB INFO')
        self.boinc_database_info = {'host': 'localhost', 'user': 'USERNAME',
                                    'passwd': 'DBPASSWORD', 'db': 'DBNAME'}

        self.project_path = ''
        if not self.project_path:
            sys.exit("Edit HostWatcher.project_path")
        self.plotter = plotter

    def retreive_earliest_host(self):
        logging.debug('Fetching newest host.')
        conn = MySQLdb.connect(**self.boinc_database_info)
        cursor = conn.cursor()

        query = ("SELECT h.id, h.domain_name, u.name, h.create_time "
                 "FROM host h, user u WHERE h.userid = u.id "
                 "AND h.create_time > %d ORDER BY h.create_time asc LIMIT 1")
        query = query % self.last_time

        logging.debug('Boinc query: %s', query)
        cursor.execute(query)

        res = cursor.fetchall()
        if res:
            hid, hname, uname, htime = res[0]
        else:
            cursor.execute("SELECT h.id, h.domain_name, u.name, h.create_time "
                           "FROM host h, user u WHERE h.userid = u.id ORDER BY "
                           "h.create_time desc LIMIT 1")
            res = cursor.fetchall()
            hid, hname, uname, htime = res[0]

        cursor.close()
        conn.close()

        logging.debug('Newest host has id: %d.', hid)
        self.last_time = htime
        self.last_id = hid

        return

    def look_for_new_hosts(self, last_time):
        logging.debug('Looking for new hosts...')
        conn = MySQLdb.connect(**self.boinc_database_info)
        cursor = conn.cursor()

        query = ("SELECT h.id, h.domain_name, u.name, h.create_time "
                 "FROM host h, user u WHERE h.userid = u.id "
                 "AND h.create_time > %d ORDER BY h.create_time desc")
        query = query % self.last_time

        logging.debug('Boinc query: %s', query)
        cursor.execute(query)

        res = cursor.fetchall()
        cursor.close()
        conn.close()

        return res

    def get_all_hosts(self):
        logging.debug('Getting all hosts...')
        conn = MySQLdb.connect(**self.boinc_database_info)
        cursor = conn.cursor()

        query = ("SELECT h.id, h.p_ncpus, h.create_time FROM host h "
                 "WHERE h.userid in (2,6) and h.domain_name regexp \"(TECH|TCC|TLC|PH|LIB)\"")

        logging.debug('Boinc query: %s', query)
        cursor.execute(query)

        res = cursor.fetchall()
        cursor.close()
        conn.close()

        return res

    def get_local_from_utcts(self, ts):
        d = datetime.datetime.utcfromtimestamp(ts)
        utctz = tz.gettz('UTC')
        local = tz.gettz('America/New_York')
        d = d.replace(tzinfo=utctz).astimezone(local).isoformat()
        return d

    def send_mail(self, body):
        # EDIT EMAIL INFO AND REMOVE sys.exit()
        sys.exit('EDIT EMAIL INFO')
        fromaddr = 'user@domain.com'
        toaddr = 'user@domain.com'
        subject = 'Subject'
        username = 'user'
        password = 'password'

        message = "\r\n".join([
                          "From: %s"%fromaddr,
                          "To: %s"%toaddr,
                          "Subject: %s"%subject,
                          "", body])

        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(username, password)
        logging.debug('Mail server login successful.')
        server.sendmail(fromaddr, toaddr, message)
        server.close()

        logging.debug('Mail sent successfully')

    def format_body(self, hosts):
        leader = ("The following hosts recently connected to the PROJECT NAME BOINC "
                  "project hosted at \r\nPROJECT URL.\r\n\r\nYou "
                  "can manage the project by logging into the following url:\r\n"
                  "PROJECT OPS URL/\r\n\r\n"
                  "Last connection_time: %s\r\n\r\nNew Hosts:\r\n") % self.get_local_from_utcts(self.last_time)

        host_fmt = "\t{create_time:<32}\t{id:>4}\t{name:<10}\t{user:>16}"
        hosts = [dict(zip(('id', 'name', 'user', 'create_time'), host)) for host in hosts]
        for host in hosts:
            host['create_time'] = self.get_local_from_utcts(host['create_time'])

        host_str = [leader] + [host_fmt.format(**host) for host in hosts] + [""]

        body = '\r\n'.join(host_str)
        return body

    def _plot(self, x, y_host, y_cores, save_name):
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

        params = dict(ls='-', color='#990033', lw='2', markeredgewidth=0., markersize=4,)
        l1, = ax1.plot_date(x, y_host, **params)
        ax1.fill_between(x, y_host, color='#990033')
        ax1.set_ylabel('Number of Hosts')

        params['color'] = '0.3'
        l2, = ax2.plot_date(x, y_cores, **params)
        ax2.fill_between(x, y_cores, color='0.3')
        ax2.set_ylabel('Number of CPU Cores')

        ax1.legend([l1, l2], ['Hosts', 'Cores'], loc=2)

        plt.setp(ax1.get_xticklabels(), visible=False)
        plt.setp(ax2.get_xticklabels(), rotation=40)

        ax1.set_xlim(min(x), datetime.datetime.today())

        plt.tight_layout()
        fig.subplots_adjust(hspace=0)
        plt.savefig(save_name, dpi=300)
        plt.close(fig)

    def plot_them(self):
        aug1 = 1438387200
        hosts = self.get_all_hosts()
        cpus, dates = map(np.array, zip(*[h[1:] for h in hosts]))

        date_hist, edges = np.histogram(dates, bins=100)
        cpu_hist, _ = np.histogram(dates, bins=100, weights=0.75*cpus)
        cum = np.cumsum(date_hist)
        cum_cpu = np.cumsum(cpu_hist)
        centers = map(datetime.datetime.fromtimestamp, (edges[:-1] + edges[1:]) / 2.)

        self._plot(centers, cum, cum_cpu, self.project_path + 'archives/host_numbers.png')

        date_mask = dates > aug1
        zoom_dates = dates[date_mask]
        zoom_cpus = cpus[date_mask]
        offset = len(dates[~date_mask])
        cpu_offset = sum(cpus[~date_mask])*0.75

        date_hist, edges = np.histogram(zoom_dates, bins=100)
        cpu_hist, _ = np.histogram(zoom_dates, bins=100, weights=0.75*zoom_cpus)
        cum = np.cumsum(date_hist) + offset
        cum_cpu = np.cumsum(cpu_hist) + cpu_offset
        centers = map(datetime.datetime.fromtimestamp, (edges[:-1] + edges[1:]) / 2.)

        self._plot(centers, cum, cum_cpu, self.project_path + 'archives/host_numbers_zoom.png')

    def run(self):
        logging.info('Host Watch starting...')
        self.retreive_earliest_host()
        try:
            while True:
                st = time.clock()

                new_hosts = self.look_for_new_hosts(self.last_time)

                if new_hosts:
                    logging.debug('Found %d new hosts.', len(new_hosts))
                    new_time = new_hosts[0][-1]

                    body = self.format_body(new_hosts)
                    logging.debug('Message formatted...')

                    self.send_mail(body)
                    self.last_time = new_time
                    if self.plotter:
                        self.plot_them()

                en = time.clock()

                time_diff = self.cycle_time - (en - st)
                if time_diff > 0:
                    time.sleep(time_diff)

        except KeyboardInterrupt:
            _quit()


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--cycle', type=int, default=21600,
                        help="Specify number of seconds between db checks")
    parser.add_argument('-v', '--verbose', action="store_true",
                        help="Enable DEBUG level logging")
    parser.add_argument('--time', type=int, default=1439405500,
                        help=("Specify time after which to record results. "
                              "Default is roughly 12PM 2015/08/12"))
    parser.add_argument('--plot', action="store_true",
                        help="Plot cumulative accumulation of hosts")

    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()

    logformat = "%(asctime)s: %(levelname)s (Line: %(lineno)d) - %(message)s"
    logdateformat = "%I:%M:%S"
    loglevel = logging.INFO
    if args.verbose:
        loglevel = logging.DEBUG

    #EDIT LOGFILE AND DELETE QUIT
    logfile = ''
    if not logfile:
        sys.exit("SPECIFY LOGFILE")
    logging.basicConfig(filename=logfile, filemode='w', level=loglevel,
                        format=logformat, datefmt=logdateformat)

    last_time = int(args.time)

    if args.plot:
        import numpy as np
        import matplotlib.pyplot as plt

    watcher = HostWatcher(args.cycle, last_time=last_time, plotter=args.plot)

    watcher.run()

def _quit(*args):
    logging.warn("Received SIGINT. Shutting down.")
    sys.exit(0)

signal.signal(signal.SIGINT, _quit)
if __name__ == "__main__":
    main()
