import subprocess
import platform
import urllib2
import time
import re

def ping(host, count=10, timeout=500):
    # Returns True if host responds to a ping request.
    # Ping parameters as function of OS
    count_arg = '-n' if platform.system().lower() == 'windows' else '-c'
    ping_cmd = ['ping', count_arg, str(count), '-W', str(timeout), str(host)]

    # Ping
    ping = subprocess.Popen(ping_cmd, stdout=subprocess.PIPE)
    result = ping.stdout.readlines()[-1]
    target = 'round-trip min/avg/max/stddev'
    if (target in result):
        min_avg_max_stddev = re.findall(r'[0-9]+[.][0-9]+', result)
        avg = min_avg_max_stddev[1]
        return (float(avg) <= timeout)
    else:
        return False

if __name__ == '__main__':
    check_dict = {}
    source = 'https://raw.githubusercontent.com/racaljk/hosts/master/hosts'
    target = '/private/etc/hosts' if platform.system().lower() == 'darwin' else '/etc/hosts'
    start = 'Modified hosts start'
    process = False
    replace = ''
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
            replace = '\n'

        # download hosts
        response = urllib2.urlopen(source)

        # check ping result
        for line in response:
            if start in line:
                process = True

            if process:
                candidates = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', line)
                if candidates:
                    ip = candidates.group()
                    if ip not in check_dict:
                        check_dict[ip] = ping(ip)

                    if not check_dict[ip]:
                        replace += '# %s' % line
                        print replace
                        continue

                replace += line
                print line

        # delete and write
        f.seek(offset)
        f.truncate()
        f.write(replace)
        print("--- %s seconds ---" % (time.time() - start_time))
