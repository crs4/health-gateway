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


import os

BASE_DIR = os.path.dirname(__file__)
CORRECT_CONSENT_ID_CR = 'consent' # correct consent in status CR
CORRECT_CONSENT_ID_AC = 'consent2' # correct consent in status AC
WRONG_CONSENT_ID = 'wrong_consent'
WRONG_CONSENT_ID2 = 'wrong_consent2'
ABORTED_CONSENT_ID = 'aborted'
ABORTED_CONSENT_ID2 = 'aborted2'
CORRECT_CONFIRM_ID = 'confirmed'
CORRECT_CONFIRM_ID2 = 'confirmed2'
WRONG_CONFIRM_ID = 'wrong_confirmed'
WRONG_CONFIRM_ID2 = 'wrong_confirmed2'
ABORTED_CONFIRM_ID = 'aborted_confirmed'
ABORTED_CONFIRM_ID2 = 'aborted_confirmed2'
PERSON_ID = 'AAABBB12C34D567E'

PROFILE_1 = {
    'code': 'PROF_001',
    'version': 'v0',
    'payload': '[{"clinical_domain": "Laboratory"}]'
}

PROFILE_2 = {
    'code': 'PROF_002',
    'version': 'v0',
    'payload': '[{"clinical_domain": "Radiology"}]'
}

SOURCE_1_ID = 'iWWjKVje7Ss3M45oTNUpRV59ovVpl3xT'
SOURCE_2_ID = 'TptQ5kPSNliFIOYyAB1tV5mt2PvwXsaS'
SOURCE_3_ID = 'AtLVwAIYrl2dx2WRcg6ZnufD1rsBO9eB'
SOURCE_1_NAME = 'source_1'
SOURCE_2_NAME = 'source_2'
SOURCE_3_NAME = 'source_3'
SOURCES_DATA = [
    {
        'source_id': SOURCE_1_ID,
        'name': SOURCE_1_NAME,
        'profile': PROFILE_1
    }, {
        'source_id': SOURCE_2_ID,
        'name': SOURCE_2_NAME,
        'profile': PROFILE_2
    }, {
        'source_id': SOURCE_3_ID,
        'name': SOURCE_3_NAME,
        'profile': PROFILE_2
    }]

PROFILES_DATA = [
    {
        'code': 'PROF_001',
        'version': 'v0',
        'payload': '[{"clinical_domain": "Laboratory"}]',
        'sources': [{
            'source_id': SOURCE_1_ID,
            'name': SOURCE_1_NAME
        }, {
            'source_id': SOURCE_2_ID,
            'name': SOURCE_2_NAME
        }]
    }
]

DEST_PUBLIC_KEY = '-----BEGIN PUBLIC KEY-----\n' \
                  'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAp4TF/ETwYKG+eAYZz3wo\n' \
                  '8IYqrPIlQyz1/xljqDD162ZAYJLCYeCfs9yczcazC8keWzGd5/tn4TF6II0oINKh\n' \
                  'kCYLqTIVkVGC7/tgH5UEe/XG1trRZfMqwl1hEvZV+/zanV0cl7IjTR9ajb1TwwQY\n' \
                  'MOjcaaBZj+xfD884pwogWkcSGTEODGfoVACHjEXHs+oVriHqs4iggiiMYbO7TBjg\n' \
                  'Be9p7ZDHSVBbXtQ3XuGKnxs9MTLIh5L9jxSRb9CgAtv8ubhzs2vpnHrRVkRoddrk\n' \
                  '8YHKRryYcVDHVLAGc4srceXU7zrwAMbjS7msh/LK88ZDUWfIZKZvbV0L+/topvzd\n' \
                  'XQIDAQAB\n' \
                  '-----END PUBLIC KEY-----'

DEST_1_NAME = 'Destination 1'
DEST_1_ID = 'vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj'
DEST_2_NAME = 'Destination 2'
DEST_2_ID = '6RtHuetJ44HKndsDHI5K9JUJxtg0vLJ3'
DISPATCHER_NAME = 'Health Gateway Dispatcher'
POWERLESS_NAME = 'Powerless Client'
