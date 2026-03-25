#%% Imports
import os, sys, logging
from datetime import datetime

#%% Functions
def makelog(scriptname, logpath):
    ### Set up logger
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    eh = logging.StreamHandler(sys.stderr)
    eh.setLevel(logging.CRITICAL)
    class StreamToLogger(object):
        """
        https://stackoverflow.com/questions/19425736/
        how-to-redirect-stdout-and-stderr-to-logger-in-python
        """
        def __init__(self, logger, level):
            self.logger = logger
            self.level = level
            self.linebuf = ''

        def write(self, buf):
            for line in buf.rstrip().splitlines():
                self.logger.log(self.level, line.rstrip())
        
        def flush(self):
            pass

    logging.basicConfig(
        level=logging.INFO,
        format=(os.path.basename(scriptname)+' | %(asctime)s | %(levelname)s | %(message)s'),
        handlers=[logging.FileHandler(logpath, mode='a'), sh, eh],
    )
    log = logging.getLogger(__name__)
    sys.stdout = StreamToLogger(log, logging.INFO)
    sys.stderr = StreamToLogger(log, logging.ERROR)

    return log


def toc(tic, year, process, path=''):
    """append timing data to meta file"""
    now = datetime.now()
    try:
        with open(os.path.join(path,'meta.csv'), 'a') as METAFILE:
            METAFILE.writelines(
                '{year},{process},{start},{stop},{elapsed}\n'.format(
                    year=year, process=process,
                    start=datetime.isoformat(tic),
                    stop=datetime.isoformat(now),
                    elapsed=(now-tic).total_seconds()
                )
            )
    except:
        print('meta.csv not found or not writeable')
        pass

def get_time(fields):
    """convert GAMS time into ISO-formatted time"""
    out = datetime.isoformat(
        datetime.strptime(fields[4]+fields[5], '%m/%d/%y%H:%M:%S')
    )
    return out

def get_delta(timestring):
    """convert hours:minutes:seconds into seconds"""
    hms = timestring.split(':')
    seconds = int(hms[0])*3600 + int(hms[1])*60 + float(hms[2])
    return seconds

def get_starts_stops(path=''):
    """get all start and stop lines from gamslog.txt"""
    starts, stops = [], []
    with open(os.path.join(path,'gamslog.txt'),'r') as f:
        for l in f:
            if l.startswith('--- Job') and 'Start' in l:
                starts.append(l)
            if l.startswith('--- Job') and 'Stop' in l:
                stops.append(l)
    return starts, stops

def time_all_gams_processes(path=''):
    """time all GAMS processes in gamslog.txt (doesn't capture year)"""
    starts, stops = get_starts_stops(path)
    outs = []
    for i in range(len(stops)):
        start, stop = starts[i].split(), stops[i].split()
        out = '{year},{process},{start},{stop},{elapsed}\n'.format(
            year=0,
            process=start[2],
            start=get_time(start),
            stop=get_time(stop),
            elapsed=get_delta(stop[7]),
        )
        outs.append(out)

    return outs

def time_last_gams_process(path='',year=0):
    """time last GAMS process in gamslog.txt"""
    starts, stops = get_starts_stops(path)
    start, stop = starts[-1].split(), stops[-1].split()
    out = '{year},{process},{start},{stop},{elapsed}\n'.format(
        year=year,
        process=start[2],
        start=get_time(start),
        stop=get_time(stop),
        elapsed=get_delta(stop[7]),
    )
    return out

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='ticker')
    parser.add_argument('-p', '--path', default='', type=str, help='case directory')
    parser.add_argument('-y', '--year', default='0', type=str, help='process year')
    args = parser.parse_args()

    try:
        with open(os.path.join(args.path,'meta.csv'), 'a') as METAFILE:
            METAFILE.writelines(
                time_last_gams_process(path=args.path, year=args.year)
            )
    except:
        print('meta.csv not found or not writeable')
        pass
