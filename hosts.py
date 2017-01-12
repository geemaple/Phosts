# !/usr/bin/env python
# -*- coding:utf-8 -*-

import multiprocessing
import subprocess
import platform
import urllib2
import time
import re

def ping(host, count=5, timeout=500):
    # Returns True if host responds to a ping request.
    # Ping parameters as function of OS
    count_arg = '-n' if platform.system().lower() == 'windows' else '-c'
    ping_cmd = ['ping', count_arg, str(count), '-W', str(timeout), str(host)]

    # # Ping
    ping = subprocess.Popen(ping_cmd, stdout=subprocess.PIPE)
    result = ping.stdout.readlines()[-1]
    target = 'round-trip min/avg/max/stddev'
    if (target in result):
        min_avg_max_stddev = re.findall(r'[0-9]+[.][0-9]+', result)
        avg = min_avg_max_stddev[1]
        result = (host, float(avg) <= timeout)
    else:
        result = (host, False)
    print 'ping test %s %s' % (host, 'success' if result[-1] else 'failed')
    return result

def start_process():
    pass

if __name__ == '__main__':
    check_dict = {}
    inputs = set()
    source = 'https://raw.githubusercontent.com/racaljk/hosts/master/hosts'
    mirror = 'https://coding.net/u/scaffrey/p/hosts/git/raw/master/hosts'
    target = '/private/etc/hosts' if platform.system().lower() == 'darwin'\
        else '/etc/hosts'
    start = 'Modified hosts start'
    process = False
    hosts = ''
    offset = 0
    start_time = time.time()

    with open(target, 'r+') as f:
        # read and find
        line = f.readline()
        while(line and start not in line):
            line = f.readline()

        offset = f.tell()
        if line:
            offset -= len(line)
        else:
            hosts = '\n'

        # download hosts
        print 'downloading hosts...'
        try:
            response = urllib2.urlopen(source)
        except:
            response = urllib2.urlopen(mirror)

        # check ping result
        print 'create testing pool...'
        pool_size = multiprocessing.cpu_count() * 2
        pool = multiprocessing.Pool(processes=pool_size,
                                    initializer=start_process)

        regex = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
        print 'parse ip to testing...'
        for line in response:
            if start in line:
                process = True

            if process:
                candidates = regex.search(line)
                if candidates:
                    ip = candidates.group()
                    inputs.add(ip)
                hosts += line

        print 'ping testing...'
        pool_outputs = pool.map_async(ping, inputs).get(1000)
        pool.close()  # no more tasks
        pool.join()   # wrap up current tasks

        for result in pool_outputs:
            if not result[-1]:
                ip = result[0]
                hosts = hosts.replace(ip, '# %s' % ip)

        print 'write to hosts file...'
        # delete and write
        f.seek(offset)
        f.truncate()
        f.write(hosts)
        print('--- all set after %s seconds ---' % (time.time() - start_time))
