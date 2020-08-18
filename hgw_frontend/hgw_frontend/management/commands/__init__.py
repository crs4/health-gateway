import functools
from time import sleep

from django.conf import settings
from django.db import Error, connection
import logging


def db_safe(TestModel, logger=None):
    """
    Wraps the call, trying to retrieve an instance of TestModel object so to ensure the db connection is alive. If not
    retries with exponential delay to restore db connection via `connection.connect()`
    :param TestModel: the django Model used to test the db connection
    :param logger: (optional) the logger to be used
    """
    logger = logging.getLogger('hgw_frontend.generic_db_safe_wrapper')

    def db_safe_wrapped(func):
        @functools.wraps(func)
        def wrapped(*args, attempt=1, **kwargs):
            try:
                TestModel.objects.first()
                return func(*args, **kwargs)
            except Error:
                retry_sleep = settings.DB_FAILURE_EXP_RETRY_BASE_PERIOD ** attempt
                if retry_sleep < settings.DB_FAILURE_MAX_RETRY_WAIT:
                    logger.warning('Error reading data from db, trying again in %s seconds', retry_sleep)
                    sleep(retry_sleep)
                    connection.connect()
                    kwargs['attempt'] = attempt + 1
                    return wrapped(*args, **kwargs)
                else:
                    logger.error('Error reading data from db - giving up after %s failed attempts', attempt)
            raise Error('Cannot connect to db')
        return wrapped
    return db_safe_wrapped
