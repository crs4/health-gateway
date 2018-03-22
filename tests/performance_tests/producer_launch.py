import subprocess

import time

import common

if __name__ == '__main__':
    parser = common.get_parser()
    parser.add_argument('-p', '--producers', help='number of producers', type=int, default=1)
    args = parser.parse_args()

    dict_args = dict(vars(args))
    dict_args.pop('producers')
    dict_args['avg_events'] /= args.producers
    producer_args = ['python3', 'mock_producer.py']

    for k, v in dict_args.items():
        producer_args += ['--{}'.format(k), str(v)]

    producer_args = ' '.join(producer_args)
    print(producer_args)
    for i in range(args.producers):
        popen = subprocess.Popen(producer_args, shell=True)
    while True:
        time.sleep(5)
