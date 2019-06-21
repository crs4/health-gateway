"""
Parse json file with topics information
"""
import argparse
import json
import os


def parse_json(topics_file_name):
    with open(topics_file_name) as topics_file:
        topics_string = topics_file.read()
        return json.loads(topics_string)


def create_topics(topics, zookeeper):
    for topic in topics:
        os.system('kafka-topics.sh --create --zookeeper {zookeeper} '
                  '--replication-factor {repl_fact} --partitions {partitions} --topic {topic_name}'
                  .format(zookeeper=zookeeper, repl_fact=topic['replication_factor'],
                          partitions=topic['partitions'], topic_name=topic['name']))

        if topic['writer'] is not None:
            os.system('kafka-acls.sh --authorizer-properties zookeeper.connect={zookeeper} --add '
                      '--allow-principal User:"CN={writer},ST=Italy,C=IT" '
                      '--topic {topic_name} --operation Write'
                      .format(zookeeper=zookeeper, writer=topic['writer'], topic_name=topic['name']))

        if topic['reader'] is not None:
            os.system('kafka-acls.sh --authorizer-properties zookeeper.connect={zookeeper} --add '
                      '--allow-principal User:"CN={reader},ST=Italy,C=IT" '
                      '--topic {topic_name} --operation Read --operation Describe'
                      .format(zookeeper=zookeeper, reader=topic['reader'], topic_name=topic['name']))


def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i', '--input_file', dest='input_file', type=str,
                        help='The json file with the topics info')
    parser.add_argument('-z', '--zookeeper', dest='zookeeper', type=str,
                        help='The uri for zookeeper')
    args = parser.parse_args()
    topics = parse_json(args.input_file)
    create_topics(topics, args.zookeeper)


if __name__ == '__main__':
    main()
