import argparse
from enum import Enum

SEC_IN_A_YEAR = 3600 * 24 * 365


class TimeUnit(Enum):
    second = 's'
    year = 'y'


def get_avg_events_sec(avg_events, time_unit):
    return avg_events / SEC_IN_A_YEAR if TimeUnit(time_unit) == TimeUnit.year else avg_events


def get_parser():
    parser = argparse.ArgumentParser(description='Mockup producer of data to test dispatcher performance')
    parser.add_argument('-d', '--doc_size', dest='doc_size', type=int, default=100000,
                        help='The mean of the gaussian of the document size in byte')
    parser.add_argument('-s', '--doc_size_sigma', dest='doc_size_sigma', type=float, default=2000, help='The mean')
    parser.add_argument('--avg_events', dest='avg_events', type=float, default=13,
                        help='Average events (per year by default, see time_unit args).')
    parser.add_argument('--time_unit', dest='time_unit', type=str, default=TimeUnit.year.value,
                        choices=[u.value for u in list(TimeUnit)],
                        help='Time unit for average events')
    return parser
