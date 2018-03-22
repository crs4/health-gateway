import argparse
import json
import pathlib
import threading

import subprocess

import os

import re

import sys

import common


def dump_metrics(metric, dest_filename, interval=1000):
    subprocess.run([
        "docker-compose exec kafka bin/kafka-run-class.sh kafka.tools.JmxTool --object-name '{}' "
        "--reporting-interval {} > {}".format(
            metric, interval, dest_filename)],
        env=os.environ, stdout=subprocess.PIPE, shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='dump kafka metrics')
    parser.add_argument('-i', dest='interval', default=1000, type=int, help='interval in ms')

    args = parser.parse_args()
    try:
        with open('.current_run') as f:
            run_info = json.load(f)
    except FileNotFoundError:
        sys.exit('Error: it seems hgw is not running')

    topics = {
        'src': common.get_sources(run_info['dir']),
        'dest': [d['id'] for d in common.get_destinations(run_info['dir'])]
    }
    metric = 'kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec,topic={}'

    # let's find the output dir (name is incremented each time)
    last_run = -1

    base_output_dir = 'metrics_d{dir}_a{avg}_sp{src_partitions}_dp{dst_partitions}_ndisp{disp_num}'.format(**run_info)
    for f in os.listdir('.'):
        r = re.match(r'{}_([0-9]+)'.format(base_output_dir), f)  # retrieving previous run dir
        last_run = int(r.group(1)) if r and int(r.group(1)) > last_run else last_run

    output_dir = '{}_{}'.format(base_output_dir, last_run + 1)
    os.mkdir(output_dir)
    print('dumping data on {}'.format(output_dir))
    for kind, id_list in topics.items():
        for id in id_list:
            threading.Thread(target=dump_metrics,
                             args=(
                                 metric.format(id), os.path.join(output_dir, '{}_{}.csv'.format(kind, id)),
                                 args.interval),
                             ).start()
