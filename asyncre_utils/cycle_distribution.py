import os
import sys
import re
import argparse
import numpy as np
import matplotlib.pyplot as plt

def get_cycle_times(directory):
    cycle_times = []
    roots = {}
    for root, dirs, files in os.walk(directory):
        max_cycle = 0
        for f in files:
            if f.endswith('.out'):
                try:
                    n = re.search(r'_(\d+).out', f).group(1)
                    n = int(n)
                    if n > max_cycle: max_cycle = n
                except Exception as e:
                    pass
        roots[root] = max_cycle
        cycle_times.append(max_cycle)

    print sorted(roots.items(), key=lambda t: t[-1])[:5]
    return np.array(cycle_times)

def hist_plot(cycle_times, directory):
    params = {'alpha': 0.6}
    plt.hist(cycle_times, bins=20, **params)

    plt.title('Distribution of maximum cycles over %i replicas for %s'%(len(cycle_times), directory))
    plt.xlabel('Number of cycles')
    plt.ylabel('Number of replicas')

    plt.savefig('cycle_time_hist.png')

def main():
    des = "Saves histogram of cycle times from specified simulation dir"
    parser = argparse.ArgumentParser(description=des)
    parser.add_argument('directory', help="system directory to search")
    args = parser.parse_args()

    directory = args.directory
    if directory.endswith('/'): directory = directory[:-1]

    cycle_times = get_cycle_times(directory)
    hist_plot(cycle_times, directory)

if __name__ == "__main__":
    main()
