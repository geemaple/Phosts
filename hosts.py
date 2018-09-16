# !/usr/bin/env python
# -*- coding:utf-8 -*-

import multiprocessing
import subprocess
import platform
import argparse
import urllib2
import time
import re
import os


def ping(args):
    # Returns True if host responds to a ping request.
    # Ping parameters as function of OS
    host, timeout, count = args
    ping_cmd = [
        'ping',
        '-n' if platform.system().lower() == 'windows' else '-c',
        str(count),
        '-W',
        str(timeout),
        '-t' if platform.system().lower() == 'darwin' else '-w',
        str(count * 2),
        str(host)
    ]

    # # Ping
    ping = subprocess.Popen(
        ping_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)

    stdout = ping.stdout.readlines()
    stderr = ping.stderr.readlines()
    result = (host, False)
    if len(stdout) > 0 and len(stderr) == 0:
        target = 'min/avg/max/'
        last_line = stdout[-1];
        if (target in last_line):
            min_avg_max_stddev = re.findall(r'[0-9]+[.][0-9]+', last_line)
            avg = min_avg_max_stddev[1]
            result = (host, float(avg) <= timeout)

    print 'ping test %s %s' % (host, 'success' if result[-1] else 'failed')
    return result

def start_process():
    pass

def download_and_process(timeout, count):
    check_dict = {}
    inputs = set()
    source = 'https://raw.githubusercontent.com/googlehosts/hosts/master/hosts-files/hosts'
    mirror = 'https://coding.net/u/scaffrey/p/hosts/git/raw/master/hosts-files/hosts'
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
        while(line and start.lower() not in line.lower()):
            line = f.readline()

        offset = f.tell()
        if line:
            offset -= len(line)
        else:
            hosts = '\n'

        # download hosts
        print 'downloading hosts...'
        try:
            response = urllib2.urlopen(source, timeout=5)
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
            if start.lower() in line.lower():
                process = True

            if process:
                if '127.0.0.1' in line or '::1' in line:
                    hosts += '# %s' % line
                    continue

                candidates = regex.search(line)
                if candidates:
                    ip = candidates.group()
                    inputs.add(ip)
                hosts += line

        print 'ping testing...'
        args = ((ip, timeout, count) for ip in inputs)
        pool_outputs = pool.map_async(ping, args).get(timeout * count)
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

if __name__ == '__main__':

    parser = argparse.ArgumentParser(usage='sudo python hosts.py -t 300 -c 5')
    parser.add_argument('-t', '--timeout', metavar='timeout', type=int, default=300, help='timeout for ping test')
    parser.add_argument('-c', '--count', metavar='count', type=int, default=5, help='ping sample count')

    if os.getuid() == 0:
        args = parser.parse_args()
        download_and_process(args.timeout, args.count)
    else:
        parser.parse_args(['-h'])
