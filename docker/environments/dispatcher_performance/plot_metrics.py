import argparse
from enum import Enum
from functools import reduce

import matplotlib
import pandas as pd
import matplotlib.pyplot as plt
import os

"""
Kafka metrics header

"time" 
"kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec,topic=m27dvayjv3ywkjmczz2d3wrkg9dicflt:Count"
"kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec,topic=m27dvayjv3ywkjmczz2d3wrkg9dicflt:EventType"
"kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec,topic=m27dvayjv3ywkjmczz2d3wrkg9dicflt:FifteenMinuteRate"
"kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec,topic=m27dvayjv3ywkjmczz2d3wrkg9dicflt:FiveMinuteRate" 
"kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec,topic=m27dvayjv3ywkjmczz2d3wrkg9dicflt:MeanRate"
"kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec,topic=m27dvayjv3ywkjmczz2d3wrkg9dicflt:OneMinuteRate"
"kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec,topic=m27dvayjv3ywkjmczz2d3wrkg9dicflt:RateUnit"

"""

matplotlib.use('GTK')


class Column(Enum):
    time = 'time'
    msg = 'msg'
    type = 'type'
    min_15_rate = '15_min_rate'
    min_5_rate = '5_min_rate'
    mean_rate = 'mean_rate'
    min_1_rate = '1_min_rate'
    rate_unit = 'rate_unit'


USED_COLUMNS = [Column.time.value, Column.msg.value, Column.min_15_rate.value, Column.min_5_rate.value,
                Column.mean_rate.value, Column.min_1_rate.value]


class JoinSuffix(Enum):
    src = '_src'
    dst = '_dst'


MSG_RATIO = 'msg_ratio'


def get_data(input_dir, sample_rate, head=0):
    data_frames = {'src': [], 'dest': []}

    for f in os.listdir(input_dir):
        if f.endswith('csv'):
            abs_fname = os.path.abspath('{}/{}'.format(input_dir, f))

            data_frame = pd.read_csv(abs_fname, skiprows=2, nrows=head if head else None,
                                     names=[c.value for c in Column],
                                     usecols=USED_COLUMNS,
                                     )
            data_frame['time'] = pd.to_datetime(data_frame['time'], unit='ms')
            data_frame['time'] = data_frame['time'].dt.round('{}ms'.format(sample_rate))
            data_frame.set_index('time', inplace=True)
            data_frames['src' if f.startswith('src') else 'dest'].append(data_frame)
    return data_frames


def plot_data(dataframe, cols, save_to_dir=None):
    ax = dataframe[cols].plot()
    ax.legend(cols)
    if save_to_dir:
        plt.savefig(os.path.join(save_to_dir, '{}.png'.format('_'.join(cols))))
    else:
        plt.show()


def sum_dataframes(*dataframes):
    return reduce(lambda x, y: x + y, dataframes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='directory with kafka metrics')

    metrics_choices = [MSG_RATIO]
    for c in USED_COLUMNS:
        metrics_choices.append(c + JoinSuffix.src.value)
        metrics_choices.append(c + JoinSuffix.dst.value)

    parser.add_argument('metrics', nargs='+', choices=metrics_choices)

    parser.add_argument('-d', dest='input_dir', default='cluster')
    parser.add_argument('--head', dest='head', help='limit on first records', type=int, default=0)
    parser.add_argument('--save', dest='save_to_dir', help='save plot instead of showing', type=str, default=None)
    parser.add_argument('-s', dest='sample_rate', help='sample rate in ms. Used for rounding datetime', type=float,
                        default=1000)
    args = parser.parse_args()
    dataframes = get_data(args.input_dir, args.sample_rate, args.head)

    src_dataframe = sum_dataframes(*dataframes['src'])
    dest_dataframe = sum_dataframes(*dataframes['dest'])
    joined_dataframe = src_dataframe.join(dest_dataframe, lsuffix=JoinSuffix.src.value, rsuffix=JoinSuffix.dst.value)

    if MSG_RATIO in args.metrics:
        joined_dataframe[MSG_RATIO] = joined_dataframe[Column.msg.value + JoinSuffix.src.value] / joined_dataframe[
            Column.msg.value + JoinSuffix.dst.value]

    plot_data(joined_dataframe, args.metrics, args.save_to_dir)
