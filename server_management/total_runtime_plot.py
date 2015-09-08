#!/usr/bin/env python
import datetime
import numpy as np
import pandas as pd
from dateutil import tz
import matplotlib.pyplot as plt
import matplotlib.colors as mplcolors
import matplotlib.colorbar as mplcolorbar
from matplotlib import dates as mpldates
from collections import defaultdict

from wu_runtime import Result, get_results, dtfloor

def total_runtime_plot(target_perc=.75):

    hosts = defaultdict(int)
    total_cpus = 0
    times = defaultdict(int)
    for result in get_results(outcome=1, userid=2):
        r = Result(*result)
        hosts[r.hostname] += 1
        total_cpus += r.N_cpus

        st, et = r.start_time, r.end_time
        d = et - st

        poll_interval = 5 # in minutes
        for t in range(0, int(d.total_seconds())+1, 60*poll_interval):
            timeval = dtfloor(st + datetime.timedelta(seconds=t))
            times[timeval] += 1

    time_values, counts = zip(*times.iteritems())
    counts = pd.Series(counts, index=time_values).sort_index()

    fig, ax = plt.subplots(figsize=(8,4))
    tu_red = '#990033'
    params = {'color': tu_red, 'lw': 2, 'ls': 'solid', 'marker': None}

    x = counts.index.to_pydatetime()
    y = counts
    target_cpus = target_perc * total_cpus

    ax.plot_date(x, y, label="Actual Usage", **params)
    ax.axhline(target_cpus, color='k', linestyle=':', label='Target Usage')
    ax.axhline(total_cpus, color='k', linestyle='--', label='Usage Limit')

    # XAXIS
    ax.xaxis.set_minor_locator(mpldates.HourLocator())
    ax.xaxis.set_major_locator(mpldates.HourLocator(np.arange(0,25,6)))
    ax.xaxis.set_major_formatter(mpldates.DateFormatter('%m-%d-%y: %H:%M'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=80)
    ax.set_xlabel('Time', size=12)

    # YAXIS
    ax.set_ylabel('CPU cores in use', size=12)
    ax.tick_params(axis='both', which='major', labelsize=8)

    ax.legend(loc=1, prop={'size':8})

    plt.tight_layout()
    fig.savefig('total_runtime_plot.png', dpi=150)

if __name__ == "__main__":
    total_runtime_plot()
