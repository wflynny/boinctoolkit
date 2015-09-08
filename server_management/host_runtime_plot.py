#!/usr/bin/env python
import datetime
from dateutil import tz
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mplcolors
import matplotlib.colorbar as mplcolorbar
from matplotlib import dates as mpldates
from mpl_toolkits.axes_grid1 import make_axes_locatable
from collections import defaultdict

from wu_runtime import Result, get_results

# DATA IO
#---------

def save_data(hosts, data, min_time):
    with open('hosts.dat', 'w') as outf:
        outf.write(min_time.isoformat() + '\n')
        for i, host in enumerate(sorted(hosts.keys())):
            outf.write(','.join([host] + map(str, data[i])) + '\n')

def load_data():
    data = []
    hosts = []
    with open('hosts.dat', 'r') as fin:
        min_time = fin.next().strip()
        min_time = datetime.datetime.strptime(min_time, '%Y-%m-%dT%H:%M:%S.%f')
        for line in fin:
            items = line.strip().split(',')
            host, nums = items[0], map(float, items[1:])
            hosts.append(host)
            data.append(nums)
        data = np.array(data)

    return min_time, hosts, data


# PLOTTING
#---------

def discrete_colorbar(N, ax, cmap):
    if type(cmap) == str:
        cmap = plt.get_cmap(cmap)
    colors_i = np.concatenate((np.linspace(0, 1., N), (0.,0.,0.,0.)))
    colors_rgba = cmap(colors_i)
    indices = np.linspace(0, 1., N+1)
    cdict = {}
    for i, key in enumerate(('red','green','blue')):
        cdict[key] = [(indices[j], colors_rgba[j-1,i], colors_rgba[j,i])
                      for j in xrange(N+1)]

    dmap = mpl.colors.LinearSegmentedColormap(cmap.name + "_%d"%N, cdict, 1024)
    mappable = mpl.cm.ScalarMappable(cmap=dmap)
    mappable.set_array([])
    mappable.set_clim(-0.5, N+0.5)
    colorbar = plt.colorbar(mappable, cax=ax)
    colorbar.set_ticks(np.linspace(0, N, N))
    colorbar.set_ticklabels(range(N))
    return colorbar

def host_runtime_plot():
    # GENERATE DATA
    hosts = defaultdict(list)
    min_time = datetime.datetime.now()
    max_time = datetime.datetime.strptime('01-01-1970', '%m-%d-%Y')
    for result in get_results(outcome=1, userid=2):
        r = Result(*result)
        hosts[r.hostname].append((r.start_time, r.end_time))
        if r.start_time < min_time: min_time = r.start_time
        if r.end_time > max_time: max_time = r.end_time

    total_time = max_time - min_time
    data = np.zeros((len(hosts), int(total_time.total_seconds()/60)))
    for i, times in enumerate([v for k,v in sorted(hosts.items())]):
        for st, et in times:
            st_ind = int((st - min_time).total_seconds()/60)
            et_ind = int((et - min_time).total_seconds()/60)
            for j in range(st_ind, et_ind):
                data[i, j] += 1

    save_data(hosts, data, min_time)

    # PLOTTING
    fig, ax = plt.subplots(figsize=(20, 8))

    N_hosts = len(hosts)
    N_bins = data.shape[1]
    host_tick_size = 100

    # IMSHOW PARAMETERS
    extent = (0, N_bins, 0, N_hosts*host_tick_size)
    cmap = 'cubehelix_r'
    imshow_params = {'extent': extent, 'alpha': 0.7, 'cmap': cmap,
                     'interpolation': 'none'}

    ax.imshow(data, **imshow_params)

    # XTICKS
    start_hour = min_time + datetime.timedelta(hours=1)
    start_hour = start_hour.replace(minute=0, second=0, microsecond=0)
    start_index = dt2hr_ind(start_hour, min_time)
    hr_multiple = 6
    xticks = np.arange(start_index, N_bins+1, 60*hr_multiple)
    ihours = lambda i: datetime.timedelta(hours=i)
    xticklabels = [(start_hour + ihours(i)).strftime('%b %d, %I %p')
                   for i in range(0, hr_multiple*len(xticks), hr_multiple)]
    xlabel = 'Time'

    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=70)
    ax.set_xlabel(xlabel)

    # YTICKS
    yticks = np.arange(N_hosts)*host_tick_size + host_tick_size/2
    yticklabels = sorted(hosts)
    ylabel = 'Host'

    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels)
    ax.set_ylabel(ylabel)

    ax.tick_params(axis='both', which='major', labelsize='10')

    # COLORBAR
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="2.5%", pad=0.05)
    colorbar = discrete_colorbar(5, cmap, cax)
    colorbar.set_label('Number of active CPU cores')

    # ADJUST FOR LONG TIMES AT THE BOTTOM
    fig.subplots_adjust(bottom=0.2, top=0.9)

    fig.savefig('host_runtime_plot.png', dpi=150)

if __name__ == "__main__":
    host_runtime_plot()
