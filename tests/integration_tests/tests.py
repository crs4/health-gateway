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


from subprocess import check_output
import time
import unittest

import os
from selenium import webdriver


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _get_system():
    return check_output(['uname', '-s']).strip().lower().decode('utf-8')


class TestFlowRequest(unittest.TestCase):
    driver_path = os.path.join(BASE_DIR, 'drivers/chromedriver_{}_64'.format(_get_system()))

    def setUp(self):
        self.driver = webdriver.Chrome(TestFlowRequest.driver_path)

    def test_create_consents(self):
        driver = self.driver
        logged = False
        for url in ("https://localhost:8001/", "https://localhost:8005/"):
            driver.implicitly_wait(120)  # this is for some slow mac
            driver.get(url)

            while not driver.title.lower().startswith('destination'):  # sometimes we have a bad gateway/not reachable error
                time.sleep(3)
                driver.refresh()

            add_button = driver.find_element_by_id("flow-add-button")
            add_button.click()
            driver.switch_to.window(driver.window_handles[1])

            if not logged:  # the second time the login is already performed
                while not driver.current_url.startswith("https://spid-testenv-identityserver"):
                    time.sleep(1)

                username = driver.find_element_by_id('username')
                password = driver.find_element_by_id('password')
                username.send_keys("paolino")
                password.send_keys("paolino")
                login = driver.find_element_by_tag_name('button')
                login.click()
                logged = True

            while not driver.current_url.startswith('https://consent'):
                time.sleep(1)

            driver.find_element_by_id('SOURCE_ENDPOINT_MOCKUP')
            driver.find_element_by_id('SOURCE_ENDPOINT_MOCKUP').click()

            confirm = driver.find_element_by_id('confirm')
            confirm.click()
            self.assertTrue(driver.find_element_by_id('operation-completed').text.startswith('The required operation has been completed'))
            close = driver.find_element_by_id('close')
            close.click()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(3)

    def tearDown(self):
        self.driver.close()


if __name__ == "__main__":
    unittest.main()