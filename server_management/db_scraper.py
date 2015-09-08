#!/usr/bin/env python
import re
import os
import sys
import time
import signal
import MySQLdb
import sqlite3
import logging
import argparse
import itertools
from operator import itemgetter

import datetime
from dateutil import tz

EPOCH = datetime.datetime(1970, 1, 1, tzinfo=tz.gettz('UTC'))

class DB(object):
    """Adapted from github.com/thegoleffect/sqlite3-python-wrapper"""
    def __init__(self, db_name, isolation_level=None):
        self.filename = db_name
        self.isolation_level = isolation_level
        self._db = None

        try:
            self.reconnect()
        except Exception as e:
            logging.critical("Exception detected!: %s", e)

    def __del__(self):
        self.close()

    def close(self):
        if getattr(self, "_db", None) is not None:
            self._db.close()
        self._db = None

    def reconnect(self):
        self.close()
        self._db = sqlite3.connect(self.filename)
        self._db.isolation_level = self.isolation_level

    def _cursor(self):
        """Returns a cursor; reconnects if disconnected."""
        if self._db is None: self.reconnect()
        return self._db.cursor()

    def _execute(self, cursor, query, parameters):
        try:
            return cursor.execute(query, parameters)
        except OperationalError as e:
            logging.critical("Error in _execute: %s", e)
            self.close()
            raise

    def execute(self, query, *parameters):
        """Executes the given query, returning the lastrowid from the query."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters)
            return cursor.lastrowid
        finally:
            cursor.close()

    def executemany(self, query, parameters):
        """Executes the given query against all the given param sequences."""
        cursor = self._cursor()
        try:
            cursor.executemany(query, parameters)
            return cursor.lastrowid
        finally:
            cursor.close()

    def query(self, query, *parameters):
        """Returns a row list for the given query and parameters."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters)
            column_names = [d[0] for d in cursor.description]
            return [Row(itertools.izip(column_names, row)) for row in cursor]
        finally:
            pass

    def get(self, query, *parameters):
        """Returns the first row returned for the given query."""
        rows = self.query(query, *parameters)
        if not rows:
            return None
        elif len(rows) > 1:
            raise Exception("Multiple rows returned from sqlite.get() query")
        else:
            return rows[0]

class Row(dict):
    """A dict that allows for object-like property access syntax."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

OperationalError = sqlite3.OperationalError

class DBScraper(object):
    def __init__(self, cycle_time, userids=None, last_time=0):
        self.cycle_time = cycle_time

        self.userids = userids

        self.last_time = last_time

        logging.debug("Cycle time: %d UIDS: %s", cycle_time, ','.join(userids))

        # EDIT DB INFO then REMOVE the quit
        sys.exit('EDIT DB INFO')
        self.boinc_database_info = {'host': 'localhost', 'user': 'USERNAME',
                                    'passwd': 'DBPASSWORD', 'db': 'DBNAME'}

        self.project_path = ''
        self.database_path = self.project_path + 'runtime.db'
        if not self.project_path:
            sys.exit("SPECIFY DBScraper.project_path!")
        self.database = DB(self.database_path, isolation_level=None)

        self.schema = (('id', 'INTEGER'),
                       ('client', 'TEXT'),
                       ('name', 'TEXT'),
                       ('cpu_time', 'REAL'),
                       ('create_time', 'INTEGER'),
                       ('sent_time', 'INTEGER'),
                       ('start_time', 'INTEGER'),
                       ('end_time', 'INTEGER'),
                       ('received_time', 'INTEGER'))

    def instantiate_db(self):
        logging.debug('Making sure table exists...')

        sql = 'CREATE TABLE IF NOT EXISTS runtime (%s)'
        sql = sql % (', '.join(' '.join(item) for item in self.schema))
        self.database.execute(sql)
        logging.debug('Table exists!')

        sql = ('SELECT received_time FROM runtime '
               'ORDER BY received_time LIMIT 1')
        res = self.database.query(sql)
        self.database.close()


        if len(res) != 0:
            res = res[0]['received_time']
        else: res = 0

        if res > 0:
            self.last_time = res
            logging.info('Picking up from where we left off. Last time = %d', res)

    def fetch_new_results(self, last_time, chunksize=1000):
        logging.debug('Fetching new results...')
        conn = MySQLdb.connect(**self.boinc_database_info)
        cursor = conn.cursor()

        if self.userids:
            userid = "AND r.userid IN (" + ','.join(self.userids) + ") "
        else: userid = ""
        query = ("SELECT h.domain_name, h.p_ncpus, r.id, "
                 "r.cpu_time, r.sent_time, r.received_time, r.stderr_out, "
                 "w.create_time, w.name "
                 "FROM host h, result r, workunit w "
                 "WHERE r.workunitid = w.id AND r.hostid = h.id "
                 "AND r.outcome = 1 AND r.server_state = 5 "
                 "%s"
                 "AND r.received_time > %d "
                 "ORDER BY r.received_time ASC "
                 "LIMIT %d")
        query = query % (userid, last_time, chunksize)
        logging.debug('Boinc query: %s', query)
        cursor.execute(query)
        res = cursor.fetchall()
        cursor.close()
        conn.close()

        return res

    def _convert_utc_to_local(self, d):
        utctz = tz.gettz('UTC')
        local = tz.gettz('America/New_York')
        d = d.replace(tzinfo=utctz)
        return d.astimezone(local)

    def to_timestamp(self, d, UTC=False):
        utctz = tz.gettz('UTC')
        local = tz.gettz('America/New_York')
        if UTC:
            d = d.replace(tzinfo=utctz)
        else:
            d = d.replace(tzinfo=local)
        return (d - EPOCH).total_seconds()

    def sanitize(self, result):
        (client, ncpus, rid, cpu_time, sent_time, received_time, stdout,
         create_time, name) = result
        logging.debug('%d %s', rid, stdout)

        result_dict = {'id': rid, 'client': client, 'name': name}
        result_dict['cpu_time'] = cpu_time

        re_str = r'([0-9]{2}:[0-9]{2}:[0-9]{2}).*wrapper:\srunning'
        first_start_match = re.findall(re_str, stdout)
        if not first_start_match:
            return
        first_start_time_items = map(int, first_start_match[0].split(':'))

        re_str = r'([0-9]{2}:[0-9]{2}:[0-9]{2}).*called\sboinc_finish'
        end_match = re.findall(re_str, stdout)
        if not end_match:
            return
        end_time_items = map(int, end_match[0].split(':'))

        duration_h = int(cpu_time/3600)
        duration_m = int(cpu_time%3600/60)
        duration_s = cpu_time%60

        received_dt = datetime.datetime.utcfromtimestamp(received_time)
        received_dt = self._convert_utc_to_local(received_dt)
        result_dict['received_time'] = self.to_timestamp(received_dt)

        sent_dt = datetime.datetime.utcfromtimestamp(sent_time)
        sent_dt = self._convert_utc_to_local(sent_dt)
        result_dict['sent_time'] = self.to_timestamp(sent_dt)

        create_dt = datetime.datetime.utcfromtimestamp(create_time)
        create_dt = self._convert_utc_to_local(create_dt)
        result_dict['create_time'] = self.to_timestamp(create_dt)

        end_time_dt = datetime.datetime(received_dt.year, received_dt.month,
                                        received_dt.day, *end_time_items)
        result_dict['end_time'] = self.to_timestamp(end_time_dt)
        start_time_dt = end_time_dt - datetime.timedelta(hours=duration_h,
                                                         minutes=duration_m,
                                                         seconds=duration_s)
        fst = dict(hour=first_start_time_items[0],
                   minute=first_start_time_items[1],
                   second=first_start_time_items[2])
        first_start_time = start_time_dt.replace(**fst)
        result_dict['start_time'] = self.to_timestamp(first_start_time)

        return result_dict

    def update_db(self, results):
        logging.info('Updating db with %d new results.', len(results))

        # list of dicts
        results = map(self.sanitize, results)
        results = [r for r in results if r is not None]

        # extra proper key order
        ig = itemgetter('id', 'client', 'name', 'cpu_time', 'create_time',
                        'sent_time', 'start_time', 'end_time', 'received_time')
        results = map(ig, results)
        received_times = sorted(map(itemgetter(-1), results))
        last_time_utc = datetime.datetime.utcfromtimestamp(received_times[-1])
        self.last_time = (last_time_utc.replace(tzinfo=tz.gettz('UTC')) - EPOCH).total_seconds()

        # Add rows
        parenq = '(' + ','.join(['?']*len(self.schema)) + ')'
        sql = 'INSERT INTO runtime VALUES ' + parenq
        self.database.executemany(sql, results)
        self.database.close()

    def run(self):
        logging.info('DB Scraper starting...')
        self.instantiate_db()
        try:
            while True:
                st = time.clock()

                new_results = self.fetch_new_results(self.last_time)

                if new_results:
                    self.update_db(new_results)

                en = time.clock()

                time_diff = self.cycle_time - (en - st)
                if time_diff > 0:
                    time.sleep(time_diff)

        except KeyboardInterrupt:
            _quit()


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--cycle', type=int, default=300,
                        help="Specify number of seconds between db checks")
    parser.add_argument('-v', '--verbose', action="store_true",
                        help="Enable DEBUG level logging")
    parser.add_argument('--userid', nargs='+', default=None,
                        help="Specify (multiple) userid(s). Default = all")
    parser.add_argument('--time', type=int, default=1439405500,
                        help=("Specify time after which to record results. "
                              "Default is roughly 12PM 2015/08/12"))

    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()

    logformat = "%(asctime)s: %(levelname)s (Line: %(lineno)d) - %(message)s"
    logdateformat = "%I:%M:%S"
    loglevel = logging.INFO
    if args.verbose:
        loglevel = logging.DEBUG

    logfile = ''
    if not logfile:
        sys.exit("SPECIFY LOGFILE")
    logging.basicConfig(filename=logfile, filemode='w', level=loglevel,
                        format=logformat, datefmt=logdateformat)

    last_time = int(args.time)

    scraper = DBScraper(args.cycle, userids=args.userid, last_time=last_time)

    scraper.run()

def _quit(*args):
    logging.warn("Received SIGINT. Shutting down.")
    sys.exit(0)

signal.signal(signal.SIGINT, _quit)
if __name__ == "__main__":
    main()
