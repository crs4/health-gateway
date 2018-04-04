import json
import os
import re

from mock import MagicMock, Mock

from hgw_common.utils import MockMessage, MockRequestHandler


class MockKafkaConsumer(object):
    """
    Simulates a KafkaConsumer
    """

    MESSAGES = []

    def __init__(self, *args, **kwargs):
        super(MockKafkaConsumer, self).__init__()
        self.first = 0
        self.end = 33
        self.counter = 0
        self.messages = {i: MockMessage(key=''.encode('utf-8'), offset=i,
                                        topic='control'.encode('utf-8'),
                                        value=json.dumps(v).encode('utf-8')) for i, v in enumerate(self.MESSAGES)}

    def beginning_offsets(self, topics_partition):
        return {topics_partition[0]: self.first}

    def end_offsets(self, topics_partition):
        return {topics_partition[0]: self.end}

    def seek(self, topics_partition, index):
        self.counter = index

    def __getattr__(self, item):
        return MagicMock()

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        try:
            m = self.messages[self.counter]
        except KeyError:
            raise StopIteration
        else:
            self.counter += 1
            return m


class MockSourceEnpointHandler(MockRequestHandler):
    CONNECTORS_PATTERN = re.compile(r'/v1/connectors/')

    def do_POST(self):
        res = super(MockSourceEnpointHandler, self).do_POST()
        if res is False:
            if self._path_match(self.CONNECTORS_PATTERN):
                payload = {}
                status_code = 200
            else:
                payload = {}
                status_code = 404
            self._send_response(payload, status_code)
