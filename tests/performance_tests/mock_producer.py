# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import json
import logging
import os
import random
import signal
import sys
import time

import common
import docker
from kafka import KafkaProducer

logger = logging.getLogger('mock_producer')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def exit_gracefully(signum, frame):
    sys.exit(1)


def get_source_id(container_number):
    source_id = None
    while source_id is None:
        try:
            with open('/data/sources_id.json', 'r') as f:
                source_id = json.load(f)[container_number - 1]
        except Exception as ex:
            logger.exception(ex)
            time.sleep(1)
    return source_id


def get_channels(container_number):
    channels = None
    while channels is None:
        try:
            with open('/data/source_channels', 'r') as f:
                channels = json.load(f)[str(container_number)]
        except Exception as ex:
            logger.exception(ex)
            time.sleep(1)
    return channels


def run(mean_doc_size, sigma_doc_size, avg_events_sec, container_idx):
    channels = int(os.environ['CHANNELS_PER_SRC'])
    logger.info("Number of channels: {}".format(channels))
    source_id = get_source_id(container_idx)
    exp_lambda = channels * avg_events_sec
    p = KafkaProducer(bootstrap_servers='kafka:9093',
                      security_protocol='SSL',
                      ssl_check_hostname=True,
                      ssl_cafile='/container/certs/ca/kafka/certs/ca/kafka.chain.cert.pem',
                      ssl_certfile='/container/certs/ca/kafka/certs/source-endpoint-mockup/cert.pem',
                      ssl_keyfile='/container/certs/ca/kafka/certs/source-endpoint-mockup/key.pem')
    logger.info('Topic for the source is: {}'.format(source_id))
    while True:
        ch_num = random.randint(0, channels - 1)
        ch_id = '{}{}'.format(source_id[:-10], ch_num)
        doc_size = round(random.gauss(mean_doc_size, sigma_doc_size))
        doc = ''.join('*' * doc_size)
        logger.debug('Sending new message of size {} to channel {} on topic {}'.format(
            sys.getsizeof(doc), ch_id, source_id))
        p.send(source_id, key=ch_id.encode('utf-8'), value=doc.encode('utf-8'))
        sleep_time = random.expovariate(exp_lambda)
        logger.debug('Sleeping {} seconds'.format(sleep_time))
        time.sleep(sleep_time)


if __name__ == '__main__':
    parser = common.get_parser()
    args = parser.parse_args()

    avg_events_sec = common.get_avg_events_sec(args.avg_events, args.time_unit)

    signal.signal(signal.SIGINT, exit_gracefully)
    logger.info('avg_events_sec %s', avg_events_sec)

    client = docker.from_env()
    container = int(client.containers.get(os.environ['HOSTNAME']).name.split('_')[-1])
    run(args.doc_size, args.doc_size_sigma, avg_events_sec, container)
